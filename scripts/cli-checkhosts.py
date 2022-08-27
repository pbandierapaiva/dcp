##
## Utiliza lib ipmi para acessar dados de hosts
##

# import libvirt
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
	db = DB()

	# somente Hosts que não são VMs 'V'
	# db.cursor.execute("Select id,nome,estado,tipo,cpu,n,mem from maq where tipo!='V'")
	db.cursor.execute("Select id,nome,estado,tipo,cpu,n,mem from maq where tipo='H'")
	todoshostsdb = db.cursor.fetchall()

	contavm = 0

	d = []
	for li in todoshostsdb:
		print("\n",li, file=output)
		db.cursor.execute("SELECT ip,rede FROM netdev WHERE maq='%s'"%li['id'])
		allIf =  db.cursor.fetchall()
		ifes={}
		for iface in allIf:
			ifes[iface['rede']]=iface['ip']

		print("IPMI: ",ifes['ipmi'],"\n",ifes,"\n\n", file=output)
		for rede in ifes:
			if rede!='ipmi':
				print(ifes[rede], file=output)
				if( fetchVMs( ifes[rede]) ): break


def fetchVMs(ip):
	status=False

	try:
		conn = libvirt.open(f'qemu+ssh://root@{ip}/system') #,auth,0)
	except libvirt.libvirtError as e:
		print(repr(e),file=sys.stderr)
		return status
	status = True
	for d in conn.listAllDomains():  #libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE):
		print(d.name(), d.isActive(), d.isPersistent(), file=output)
		raiz= ET.fromstring(d.XMLDesc())
		for el in raiz:
			if el.tag=='devices':
				for el2 in el:
					if el2.tag=='interface':
						for el3 in el2:
							if el3.tag=='mac':
								print("\t",el3.attrib['address'], file=output)
	output.flush()
	return status

output=open("output.log","w+")

allHosts()
