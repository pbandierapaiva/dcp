#
# Conecta em todas as máquinas físicas marcadas como Host e resgata VMs e seus estados
#

import mariadb
import re
import os
import subprocess

from conexao import conexao, rootpw
from paramiko.client import SSHClient, AutoAddPolicy

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
	tudo = db.cursor.fetchall()

	contavm = 0

	d = []
	for li in tudo:
		hostOK = False

		print("Host: %s (%d)"%(li["nome"],li["id"]))

		db.cursor.execute("Select rede,ip from netdev where maq='"+str(li['id'])+"'")
		interfaces = db.cursor.fetchall()

		li['redes'] = []
		for iface in interfaces:
			if iface["rede"]=='ipmi': continue
			li['redes'].append(iface["ip"])

		# print(li) # Host

		for ip in li['redes']:
			ret = vmhostlist(ip)
			if ret['STATUS']=="OK":
				hostOK=True
				break

		if not hostOK:
			print("Problemas com host: ",li)
			continue

		# ret => vm status
		sall = set(  ret["all"] )
		for vm in sall:
			if vm in ret["on"]: estado = "1"
			elif vm in ret['off']: estado = "0"
			else: estado = "-1"

			inscmd =  """INSERT INTO maq (nome, estado, tipo, hospedeiro)
						VALUES ('%s','%s','%s','%s')"""%(vm,estado,'V',li['id'])
			try:
				status = db.cursor.execute(inscmd)
			except:
				print("Erro inserção BD >>"+inscmd)
				input("	")
			contavm+=1
			print("\tvm: %s (%s)"%(vm,estado))

	db.commit()
	print("Total de VMs: %d"%contavm)

def vmhostlist(ip):
	client = SSHClient()
	client.load_system_host_keys()
	client.load_host_keys("/home/paiva/.ssh/known_hosts")
	try:
		client.connect(ip,username='root',password=rootpw)
	except Exception as ex:
		template = "An exception of type {0} occurred. Arguments:\n{1!r}"
		m = template.format(type(ex).__name__, ex.args)
		return {'STATUS':'ERROR', 'MSG':m}

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

	return {"on":on,"off":off, "all":all, "other":other, "STATUS":"OK", "MSG":err}


allHosts()
