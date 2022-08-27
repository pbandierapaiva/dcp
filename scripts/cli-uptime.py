##
## Utiliza ssh root nos hosts para verificar uptime
##

# import libvirt
import sys

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
		print("\n",li)
		db.cursor.execute("SELECT ip,rede FROM netdev WHERE maq='%s'"%li['id'])
		allIf =  db.cursor.fetchall()
		ifes={}
		for iface in allIf:
			ifes[iface['rede']]=iface['ip']

		print("IPMI: ",ifes['ipmi'],"\n",ifes,"\n\n")
		for rede in ifes:
			print('\n----')
			if rede!='ipmi':
				print(ifes[rede])
				if( fetchUptime( ifes[rede]) ): break


def fetchUptime(ip):
	status=False
	# print(ip)

allHosts()
