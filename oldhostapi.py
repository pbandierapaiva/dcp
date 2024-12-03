## hostapi.py - servidor FASTAPI para monitoramento do DC

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from pyghmi.ipmi import command as IPMI

# from fastapi import FastAPI, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# from datetime import datetime, timedelta

# driver mysql
# import mariadb
# import mysql.connector as mariadb
import re
import os
import subprocess

from database import DB, NetDev, HostInfo 
from agendador import agendaMonitoramento
from conexao import conexao, botToken

# from conexao import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES,ADMIN_PASSWORD

from paramiko.client import SSHClient, AutoAddPolicy

app = FastAPI()
agendaMonitoramento()


# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# async def get_current_admin(token: str = Depends(oauth2_scheme)):
#     """Extract and verify the admin token."""
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username != "admin":
#             raise HTTPException(status_code=403, detail="Not an admin user")
#         return username
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")


# # Routes
# @app.post("/token")
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     """Login endpoint to authenticate the admin."""
#     if form_data.username != "admin" or form_data.password != ADMIN_PASSWORD:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = create_access_token(data={"sub": "admin"})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/admin/command")
# async def admin_command(admin: str = Depends(get_current_admin)):
#     """Admin-only command."""
#     return {"message": "You have access to admin commands.", "user": admin}









##########################################################
app.mount("/web", StaticFiles(directory="web"), name="web")

@app.get("/")
async def root():
    return RedirectResponse("/web/host.html")

# BASE_URL = f"https://api.telegram.org/bot{botToken}"

# # Entrada para Telegram webhook
# @app.post("/webhook")
# async def handle_webhook(request: Request):
#     data = await request.json()  # Get the JSON payload from Telegram
#     print("Recebeu update:", json.dumps(data, indent=2))

#     # Process the update
#     if "message" in data:
#         chat_id = data["message"]["chat"]["id"]
#         text = data["message"].get("text", "")

#         # Respond to the user
#         reply_text = f"You said: {text}"
#         send_message(chat_id, reply_text)

#     return {"status": "ok"}

# def send_message(chat_id: int, text: str):
#     """
#     Envia mensagem via Telegram bot.
#     """
#     url = f"{BASE_URL}/sendMessage"
#     payload = {
#         "chat_id": chat_id,
#         "text": text,
#     }
#     response = requests.post(url, json=payload)
#     if response.status_code != 200:
#         print(f"Falha ao enviar mensagem: {response.text}")

# # Configura o webhook do Telegram
# @app.on_event("startup")
# def set_webhook():
#     webhook_url = "https://your-server-url/webhook" 
#     url = f"{BASE_URL}/setWebhook"
#     payload = {"url": webhook_url}
#     response = requests.post(url, json=payload)
#     if response.status_code == 200:
#         print("Webhook set successfully!")
#     else:
#         print(f"Failed to set webhook: {response.text}")



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
	

	db = DB()
	db.cursor.execute(sql)
	results = db.cursor.fetchall()
	return JSONResponse(content=jsonable_encoder(results))	

@app.get("/hosts")
async def host():
	# sql = '''
	# SELECT 
	# 	servidor.*,
	# 	servidor_log.ts,
	# 	servidor_log.state,
	# 	servidor_log.temp,
	# 	servidor_log.rodada,
	# 	servidor_log.DC AS DC_log
	# FROM servidor
	# INNER JOIN servidor_log ON servidor.id = servidor_log.id
	# WHERE servidor_log.rodada = (
	# 	SELECT MAX(rodada) FROM servidor_log
	# );
	# '''
	sql="""
		WITH ranked_records AS (
			SELECT 
				servidor.*,
				servidor_log.ts,
				servidor_log.state,
				servidor_log.temp,
				servidor_log.rodada,
				servidor_log.DC AS DC_log,
				ROW_NUMBER() OVER (PARTITION BY servidor.id ORDER BY servidor_log.ts DESC) AS rnk
			FROM servidor
			INNER JOIN servidor_log ON servidor.id = servidor_log.id
			WHERE servidor.habilitado = 1 
			AND servidor_log.rodada = (SELECT MAX(rodada) FROM servidor_log)
		)
		SELECT * 
		FROM ranked_records
		WHERE rnk = 1;

	"""
	db = DB()
	db.cursor.execute(sql)
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

def pegaCredenciais(hostid):
	db = DB()
	db.cursor.execute("Select id,Nome,IPMI_IP,senhaIPMI from servidor where id=%s"%hostid)
	credenciais = db.cursor.fetchone()
	return {"ip":credenciais["IPMI_IP"],"senha":credenciais["senhaIPMI"]}

@app.get("/hosts/{hostid}/status")
async def pegaStatus(hostid):    # ip, senha):	
	credenciais = pegaCredenciais(hostid)
	ip = credenciais["ip"]
	senha = credenciais["senha"]

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

@app.get("/hosts/{hostid}/power/{cmd}")
async def pegaStatus(hostid, cmd):    # ip, senha):	
	if cmd.upper() not in ("ON","SOFT","OFF"):
		print(f"Comando inválido {cmd.upper()}")
		return
	credenciais = pegaCredenciais(hostid)
	ip = credenciais["ip"]
	senha = credenciais["senha"]
	ipmi_conn = IPMI.Command(bmc=ip, userid='admin', password=senha, keepalive=False)
	estado = ipmi_conn.set_power(cmd, wait=True)
	return estado	




#############################################################
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

