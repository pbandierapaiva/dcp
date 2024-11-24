## hostapi.py - servidor FASTAPI para monitoramento do DC

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from pyghmi.ipmi import command as IPMI

# driver mysql
# import mariadb
# import mysql.connector as mariadb
import re
import os
import subprocess

from database import DB, NetDev, HostInfo 
from agendador import agendaMonitoramento
#from conexao import conexao, rootpw

from paramiko.client import SSHClient, AutoAddPolicy

app = FastAPI()
agendaMonitoramento()

app.mount("/web", StaticFiles(directory="web"), name="web")

@app.get("/")
async def root():
    return RedirectResponse("/web/host.html")

@app.get("/DC")
async def DCstatus():

	## SQL para pegar as últimas sondagens de todos os servidores ligados
	## e calcular a temperatura média dos ambientes STI e DCP
	sql = """
	SELECT 
	DC,
	ROUND(AVG(temp), 2) AS avg_temp,
	SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END) AS stateON,
	SUM(CASE WHEN state = 1 THEN 1 ELSE 0 END) AS stateOFF,
	rodada
	FROM servidor_log
	WHERE rodada = (
	SELECT MAX(rodada) FROM servidor_log
	)
	GROUP BY DC;
	"""

	# sql =	"""
	# 	WITH ranked_records AS (
	# 		SELECT
	# 			servidor.id,
	# 			nome,
	# 			DC,
	# 			ts,
	# 			state,
	# 			temp,
	# 			ROW_NUMBER() OVER (PARTITION BY servidor.id ORDER BY ts DESC) AS rnk
	# 		FROM servidor_log
	# 		INNER JOIN servidor ON servidor.id = servidor_log.id
	# 	)
	# 	SELECT 
	# 		DC,
	# 		ROUND( AVG(temp), 2) AS avg_temp,
	# 		MAX(ts) AS latest_ts
	# 	FROM ranked_records
	# 	WHERE temp IS NOT NULL AND state > 0 AND rnk = 1
	# 	GROUP BY DC;servidor_log;

	# 	SELECT state, COUNT(*) AS N
	# 	FROM (
	# 		SELECT 
	# 			id, 
	# 			state, 
	# 			ts,
	# 			ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC) AS rnk
	# 		FROM servidor_log
	# 	) ultimosRegistros
	# 	WHERE rnk = 1
	# 	GROUP BY state;
	# 	"""
	db = DB()
	db.cursor.execute(sql)
	results = db.cursor.fetchall()
	return JSONResponse(content=jsonable_encoder(results))	
	# # Fetch all results from each statement
	# results = []
	# for result in db.cursor:
	# # for result in cursor:
	# 	try:
	# 		# Only fetch rows for SELECT queries
	# 		if result.with_rows:
	# 			results.append(result.fetchall())
	# 	except AttributeError:
	# 		continue  # Skip non-SELECT queries

	# db.cursor.close()

	# # Separate the results for the two queries
	# medias = results[0] if len(results) > 0 else []
	# contadores = results[1] if len(results) > 1 else []
	# # 	if result.with_rows:  # Process only if the result set contains rows
	# # 		results.append(result.fetchall())

	# # # Separate results for the two queries
	# # medias, contadores = results

	# # medias = db.cursor.fetchall()
	# # db.commit()

	# # db.cursor.execute(sqlContaONOFF)
	# # contadores = db.cursor.fetchall()
	# return JSONResponse(content=jsonable_encoder({"medias":medias,"contadores":contadores}))
	# # return JSONResponse(content=jsonable_encoder({"medias":medias}))	

@app.get("/hosts")
async def host():
	db = DB()
	# somente Hosts que não são VMs 'V'
	db.cursor.execute("Select * from servidor")
	# db.cursor.execute("Select id,nome,comentario,CONVERT(estado,CHAR)as estado,CONVERT(tipo,CHAR) as tipo,cpu,n,mem from maq where tipo!='V'")
	tudo = db.cursor.fetchall()
	return JSONResponse(content=jsonable_encoder(tudo))
	
##  /hosts
@app.get("/hosts1")
async def host():
	db = DB()

	# somente Hosts que não são VMs 'V'
	db.cursor.execute("Select id,nome,comentario,estado,tipo,cpu,n,mem from maq where tipo!='V'")
	# db.cursor.execute("Select id,nome,comentario,CONVERT(estado,CHAR)as estado,CONVERT(tipo,CHAR) as tipo,cpu,n,mem from maq where tipo!='V'")
	tudo = db.cursor.fetchall()

	d = []
	for li in tudo:
		db.cursor.execute("Select rede,ip from netdev where maq='"+str(li['id'])+"'")
		interfaces = db.cursor.fetchall()

		li['redes'] = {}
		for iface in interfaces:
			li['redes'][iface["ip"]]=iface["rede"]
		d.append(li)
	return JSONResponse(content=jsonable_encoder(d))

@app.get("/hosts/{hostid}")
async def hostinfoById(hostid):
	db = DB()

	db.cursor.execute("Select * from maq where id='"+hostid+"'")
	h = db.cursor.fetchone()

	if not h:
		return None

	db.cursor.execute("Select rede,ip from netdev where maq='"+str(h['id'])+"'")
	interfaces = db.cursor.fetchall()

	h['redes'] = {}
	for iface in interfaces:
		h['redes'][iface["ip"]]=iface["rede"]
	return JSONResponse(content=jsonable_encoder(h))

@app.get("/hosts/{hostid}/status")
async def pegaStatus(hostid):    # ip, senha):	
	ipmi_conn = None
	db = DB()
	db.cursor.execute("Select id,Nome,IPMI_IP,senhaIPMI from servidor where id=%s"%hostid)
	credenciais = db.cursor.fetchone()
	ip = credenciais["IPMI_IP"]
	senha = credenciais["senhaIPMI"]

	try:
		ipmi_conn = IPMI.Command(bmc=ip, userid='admin', password=senha) #, keepalive=False)
		valor = ipmi_conn.get_power().get('powerstate')                                                        
																										
	except Exception as e:                                                                                     
		print(f"Erro: {e}")                                                                                                                                                           
		return JSONResponse(content=jsonable_encoder({None,None}))																										
																												
	temp = None                                                                                            
	if valor == 'on':                                                                                      
		try:                                                                                               
			temp = ipmi_conn.get_sensor_reading('System Temp').value                                       
		except:                                                                                            
			temp = None                                                                                    
	return JSONResponse(content=jsonable_encoder({"power":valor == 'on',"temp":temp}))

@app.get("/hosts/{hostid}/powerstatus")
async def hostinfoPowerStatus(hostid):
	db = DB()

	db.cursor.execute("Select netdev.ip, maq.altsec from maq,netdev where maq.id=netdev.maq AND maq.id='"+hostid+"' AND netdev.rede='ipmi'")
	h = db.cursor.fetchone()

	if not h:
		o = {"hostid":hostid,"STATUS":"ERRO", "msg":"Não encontrado no banco" }
		return JSONResponse(content=jsonable_encoder(o))
	ip = h["ip"]
	if h["altsec"]:
		executa = ['ipmitool','-c', '-I','lanplus','-H', ip, '-U', 'admin', '-P', h["altsec"],'power','status']
	else:
		executa = ['ipmitool','-c', '-I','lanplus','-H', ip, '-U', 'admin', '-P', rootpw,'power','status']

	output = subprocess.run(executa, capture_output=True, text=True		)

	o = {"hostid":hostid,"ip":ip}
	if output.returncode==1:
		o["STATUS"]='ERRO'
		o["msg"]= output.stderr
	else:
		o["STATUS"]='OK'
		mensagem = str(output.stdout).strip()
		o["msg"]= mensagem
		ultima = mensagem.split()[-1]
		if str(ultima)=='on':
			o["power"]= "1"
		else:
			o["power"]= "0"
	return JSONResponse(content=jsonable_encoder(o))

@app.get("/hosts/{hostid}/temp")
async def hostinfoPowerStatus(hostid):
	db = DB()

	db.cursor.execute("Select netdev.ip, maq.altsec from maq,netdev where maq.id=netdev.maq AND maq.id='"+hostid+"' AND netdev.rede='ipmi'")
	h = db.cursor.fetchone()

	if not h:
		o = {"hostid":hostid,"STATUS":"ERRO", "msg":"Não encontrado no banco" }
		return JSONResponse(content=jsonable_encoder(o))
	ip = h["ip"]

	if h["altsec"]:
		pw = h["altsec"]
	else:
		pw = rootpw
	executa = ['ipmi-sensors','-h', ip, '-u', 'admin', '-p', pw, "-r","138"]

	output = subprocess.run(executa, capture_output=True, text=True		)
	return JSONResponse(content=jsonable_encoder(output))

@app.get("/hosts/{hostid}/ambient")
async def hostinfoPowerStatus(hostid):
	db = DB()

	db.cursor.execute("Select netdev.ip, maq.altsec from maq,netdev where maq.id=netdev.maq AND maq.id='"+hostid+"' AND netdev.rede='ipmi'")
	h = db.cursor.fetchone()

	if not h:
		o = {"hostid":hostid,"STATUS":"ERRO", "msg":"Não encontrado no banco" }
		return JSONResponse(content=jsonable_encoder(o))
	ip = h["ip"]
	print(ip)
	if h["altsec"]:
		executa = ['ipmitool','-c', '-I','lanplus','-H', ip, '-U', 'admin', '-P', h["altsec"], "sensor"] #, "get", "CPU1 Temp"]
	else:
		executa = ['ipmitool','-c', '-I','lanplus','-H', ip, '-U', 'admin', '-P', rootpw, "sensor"] #	, "get", "CPU1 Temp"]

	out = subprocess.run(executa, capture_output=True)

	o = {"hostid":hostid,"ip":ip}
	if out.returncode==1:
		o["STATUS"]='ERRO'
		o["msg"]= out.stderr
	else:
		o["STATUS"]='OK'
		od = {}
		for it in out.stdout.decode().split("\n"):
			parts = it.split(",")
			if parts[0] == "CPU1 Temp":
				if parts[1]!='na':
					o["CPU_TEMP"] = float(parts[1])
			if parts[0] == "System Temp":
				if parts[1]!='na':
					o["SYS_TEMP"] = float(parts[1])
			if parts[0] == "Ambient Temp":
				if parts[1]!='na':
					o["AMBIENT"] = float(parts[1])
			if parts[0] == 	"Inlet Temp":
				if parts[1]!='na':
					o["INLET"] = float(parts[1])
			if parts[0] == 	"Exhaust Temp":
				if parts[1]!='na':
					o["EXHAUST"] = float(parts[1])
			if parts[0] == 	"Temp":
				if parts[1]!='na':
					o["TEMP"] = float(parts[1])
			# od[parts[0]]=parts[1:]
		# o["msg"]= od  #output.stdout #.read()
	# return mensagem
	return JSONResponse(content=jsonable_encoder(o))

@app.get("/hosts/{host_id}/vm")
async def getVMInfo(host_id):
	db = DB()
	db.cursor.execute("Select * from maq where hospedeiro='"+host_id+"'")
	h = db.cursor.fetchall()
	return JSONResponse(content=jsonable_encoder(h))

@app.put("/hosts/{hostid}/powerstatus/{estado}")
async def hostinfoPowerStatus(hostid,estado):
	db = DB()
	try:
		db.cursor.execute("UPDATE maq SET estado='%s' WHERE id=%s"%(estado,hostid))
		print("UPDATE maq SET estado='%s' WHERE id=%s"%(estado,hostid))
		db.commit()
	except: 
		print("ERRO DE UPDATE")

@app.post("/hosts/{host_id}/status/{status}")
async def estadoHost(host_id, status):
	if status not in ["on","off","other","1","0","-1"]:
		return JSONResponse(content=jsonable_encoder({"STATUS":"ERROR","MSG":"Status not on or off"}))
	if status=="on" or status=="1":
		s="1"
	elif status=="off" or status=="0":
		s="0"
	else: s = "-1"
	sql = "UPDATE maq SET estado='%s' WHERE id=%s"%(s,host_id)
	db = DB()
	try:
		status = db.cursor.execute(sql)
		db.commit()
	except Exception as ex:
		return JSONResponse(content=jsonable_encoder({'STATUS':'ERROR', 'MSG':ex.args}))
	return JSONResponse(content=jsonable_encoder({"STATUS":"OK"}))

@app.post("/hosts/{host_id}/tipo/{tipo}")
async def tipoMaq(host_id, tipo):
	if tipo not in ["H","S","V"]:
		return JSONResponse(content=jsonable_encoder({"STATUS":"ERROR","MSG":"Status not on or off"}))
	sql = "UPDATE maq SET tipo='%s' WHERE id=%s"%(tipo,host_id)
	db = DB()
	try:
		status = db.cursor.execute(sql)
		db.commit()
	except Exception as ex:
		return JSONResponse(content=jsonable_encoder({'STATUS':'ERROR', 'MSG':ex.args}))
	return JSONResponse(content=jsonable_encoder({"STATUS":"OK"}))

@app.post("/hosts/{host_id}")
async def atualizaHost(item: HostInfo):
		setexpression = " SET nome='%s',comentario='%s', estado='%s', tipo='%s', so='%s', kernel='%s', cpu='%s', n=%d, mem=%d "%\
			(item.nome, item.comentario, item.estado, item.tipo, item.so, item.kernel, item.cpu, item.n, item.mem)

		if item.hospedeiro:
			setexpression+= ", hospedeiro=%d"%(item.hospedeiro)
		cmdupd = "UPDATE maq  "+setexpression+"  WHERE id=%d"%(item.hostid)

		db = DB()
		try:
			status = db.cursor.execute(cmdupd)
			db.commit()
		except:
			return JSONResponse(content=jsonable_encoder({"STATUS":'ERROR: updating database'}))
		return JSONResponse(content=jsonable_encoder({"data":item.hostid, "STATUS":"OK"}))

@app.get("/busca/{nome}")
async def hostsearch(nome):
	db = DB()

	db.cursor.execute("Select * from maq where nome LIKE '%"+nome+"%'")
	hostlist = db.cursor.fetchall()
	if not hostlist:
		return JSONResponse(content=jsonable_encoder([]))

	for h in hostlist:
		db.cursor.execute("Select rede,ip from netdev where maq='"+str(h['id'])+"'")
		interfaces = db.cursor.fetchall()
		h['redes'] = {}
		for iface in interfaces:
			h['redes'][iface["ip"]]=iface["rede"]

	return JSONResponse(content=jsonable_encoder(hostlist))

@app.get("/nets")
async def listaNets():
	db = DB()
	db.cursor.execute("Select * from rede")
	return JSONResponse(content=jsonable_encoder(db.cursor.fetchall()))

@app.put("/netdev")
async def criaNetDev( nd: NetDev):

	ipValido = True
	if not re.findall("\\d+\\.\\d+\\.\\d+\\.\\d+", nd.ip):
		ipValido=False
	else:
		for n in nd.ip.split('.'):
			try:
				if int(n)<0 or int(n)>254:
					ipValido=False
			except:
				ipValido=False
	if not ipValido:
		return JSONResponse(content=jsonable_encoder({"STATUS":'ERROR: invalid address'}))
	cmdins = "INSERT INTO netdev (ip,ether,rede,maq) VALUES ('%s','%s','%s',%d)"%(nd.ip,nd.ether,nd.rede,nd.maq)
	db = DB()
	try:
		status = db.cursor.execute(cmdins)
		db.commit()
	except:
		return JSONResponse(content=jsonable_encoder({"STATUS":'ERROR: duplicate IP'}))

	# print(str(dir(db.cursor)))
	return JSONResponse(content=jsonable_encoder({"STATUS":'OK'}))

@app.delete("/netdev/{ip}", status_code=204)
def delete_book(ip: str) -> None:
	cmddel = "DELETE FROM netdev WHERE ip='%s' "%(ip)
	db = DB()
	status = db.cursor.execute(cmddel)
	db.commit()

@app.get("/vmhosts/{ip}")
def vmhostlist(ip):
	client = SSHClient()
	client.load_system_host_keys()
	client.load_host_keys("/home/paiva/.ssh/known_hosts")
	try:
		client.connect(ip,username='root',password=rootpw)
	except Exception as ex:
		template = "An exception of type {0} occurred. Arguments:\n{1!r}"
		m = template.format(type(ex).__name__, ex.args)
		return JSONResponse(content=jsonable_encoder({'STATUS':'ERROR', 'MSG':m}))

	all=[]
	on=[]
	off=[]
	err=""
	stdin, stdout, stderr = client.exec_command('virsh list --name --all')
	for l in stdout:
			if l.strip()=='': break
			all.append(l.strip())
	for l in stderr:
		err+=l
	stdin, stdout, stderr = client.exec_command('virsh list --name')
	for l in stdout:
			if l.strip()=='': break
			on.append(l.strip())
	for l in stderr:
		err+=l
	stdin, stdout, stderr = client.exec_command('virsh list --name --inactive')
	for l in stdout:
			if l.strip()=='': break
			off.append(l.strip())
	for l in stderr:
		err+=l
	other = list( set(all) - (set(on)|set(off)))
	return JSONResponse(content=jsonable_encoder({"on":on,"off":off, "all":all, "other":other, "STATUS":"OK", "MSG":err}))

@app.get("/vmhosts/{ip}/release")
async def catrelease(ip):
	ret = {'so':'','kernel':'',"STATUS":'OK'}
	client = SSHClient()
	client.load_system_host_keys()
	client.load_host_keys("/home/paiva/.ssh/known_hosts")
	client.connect(ip,username='root',password=rootpw)
	stdin, stdout, stderr = client.exec_command("cat /etc/system-release")
	try:
		ret['so'] = stdout.read()
	except:
		ret["STATUS"]+="SO: "+ str( stderr.read() )

	stdin, stdout, stderr = client.exec_command("uname -a")
	try:
		ret['kernel'] = stdout.read()   #.split(' ')[2]
	except:
		ret["STATUS"]+="Kernel " + str( stderr.read() )

	stdin, stdout, stderr = client.exec_command("grep 'model name' /proc/cpuinfo")
	try:
		li = stdout.readlines()

		ret["n"] = len(li)
		ret['cpu'] = li[0].split('\t: ')[1]
	except:
		ret["STATUS"]+="CPU " + str( stderr.read() )

	stdin, stdout, stderr = client.exec_command("free -h | grep Mem:")
	try:
		li = stdout.readline()
		ret["mem"] = " ".join(li.split()).split()[1]
	except:
		ret["STATUS"]+="CPU " + str( stderr.read() )
	return JSONResponse(content=jsonable_encoder(ret))

@app.get("/vm/{host_id}/{nome_vm}")
async def getVM(nome_vm):
		db = DB()
		db.cursor.execute("Select * from maq where tipo='V' AND nome='"+nome_vm+"'")
		h = db.cursor.fetchone()
		if not h: return JSONResponse(content=jsonable_encoder({"STATUS":False,"vm":nome_vm}))
		db.cursor.execute("Select rede,ip from netdev where maq='"+str(h['id'])+"'")
		interfaces = db.cursor.fetchall()
		h["STATUS"] = True
		h['redes'] = {}
		for iface in interfaces:
			h['redes'][iface["ip"]]=iface["rede"]
		return JSONResponse(content=jsonable_encoder(h))

@app.put("/vm")
async def criaVM(i: HostInfo):
	inscmd =  "INSERT INTO maq (nome, estado, tipo, hospedeiro) VALUES ('%s','%s','%s','%s')"%(i.nome,i.estado,i.tipo,i.hospedeiro)
	db = DB()
	try:
		status = db.cursor.execute(inscmd)
		db.commit()
	except:
		return JSONResponse(content=jsonable_encoder({"STATUS":'ERROR: inserting into database'}))
	return JSONResponse(content=jsonable_encoder({"data":i.hostid, "STATUS":"OK"}))

@app.delete("/vm/{hostid}/{vmname}", status_code=204)
def delete_vm(hostid:int, vmname: str) -> None:
	cmddel = "DELETE FROM maq WHERE hospedeiro=%d AND nome='%s' "%(hostid,vmname)
	db = DB()
	status = db.cursor.execute(cmddel)
	db.commit()

