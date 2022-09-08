#!bin/python
##
## Utiliza libvirt para acessar dados de VMs rodando em todos os hosts ligados
##

import libvirt
import sys
# import xml
import xml.etree.ElementTree as ET

import mariadb
from conexao import conexao, rootpw

class DB:
	def __init__(self):
		self.con= mariadb.connect(**conexao)
		self.cursor= self.con.cursor(dictionary=True)
	def commit(self):
		self.con.commit()

def allHosts():
	print("Conectando todos os hospedeiros registrados...")
	db = DB()

	# somente Hosts que não são VMs 'V'
	# db.cursor.execute("Select id,nome,estado,tipo,cpu,n,mem from maq where tipo!='V'")
	db.cursor.execute("Select id,nome,estado,tipo,cpu,n,mem from maq where tipo='H' and estado='1'")
	todoshostsdb = db.cursor.fetchall()

	contavm = 0

	d = []
	for li in todoshostsdb:
	
		db.cursor.execute("SELECT ip,rede FROM netdev WHERE maq='%s'"%li['id'])
		allIf =  db.cursor.fetchall()

		print(li["nome"])
		for iface in allIf:
			if iface["rede"]!="ipmi":
				print(iface["ip"])
				vms = fetchVMs( iface["ip"]) 
				if vms==None: continue
				else: 
					sqldel = "DELETE FROM maq WHERE hospedeiro=%s"%li['id']
					db.cursor.execute(sqldel)
					# print(sqldel)
					for vm in vms:
						if 'port' in vm["graph"]:
							# print(vm["graph"]["port"])
							portavnc = vm["graph"]["port"]
						else:
							portavnc = '0'
						sqlins = """
						INSERT INTO maq (nome,estado,tipo,hospedeiro,vncport,mem,n)
						VALUES ('%s','%s','V','%s',%s,%s,%s)
						"""%(vm["nome"],vm["ligada"],li['id'],portavnc,vm["mem"],vm["cpu"])
						db.cursor.execute(sqlins)
						# print(sqlins)
					break
		db.commit()

	print("Operação concluída")

def fetchVMs(ip):
	try:
		conn = libvirt.open(f'qemu+ssh://root@{ip}/system') #,auth,0)
	except libvirt.libvirtError as e:
		print(repr(e),file=sys.stderr)
		return None

	vms=[]
	for d in conn.listAllDomains():  #libvconn.listAllDomains()irt.VIR_CONNECT_LIST_DOMAINS_ACTIVE):
		maq= {"nome":d.name(), "ligada":d.isActive(), "persistente": d.isPersistent()}

		# print("\t", d.name(), d.isActive(), d.isPersistent())
		raiz = ET.fromstring(d.XMLDesc())
		el = raiz.find('currentMemory')
		if el!=None:
			maq["mem"] =  el.text
			# print('\t\tMem: ', el.text)
		el = raiz.find('vcpu')
		if el!=None: 
			maq["cpu"]= el.text
			# print('\t\tCPUs: ', el.text)
		el = raiz.find('vcpu')
		devs = raiz.find('devices').find('graphics').attrib
		maq["graph"] = devs
		vms.append(maq)
		continue

		# print(d.name(), d.isActive(), d.isPersistent(), file=output)
		
		raiz= ET.fromstring(d.XMLDesc())
		for el in raiz:
			if el.tag=='devices':
				for el2 in el:
					if el2.tag=='interface':
						for el3 in el2:
							if el3.tag=='mac':
								print("\t",el3.attrib['address'], file=output)
	output.flush()

	return vms

output=open("output.log","w+")

allHosts()
