#!bin/python
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

	# verifica status (ON/OFF) somente Hosts que não são VMs 'V'
	# db.cursor.execute("Select id,nome,estado,tipo,cpu,n,mem from maq where tipo!='V'")
	db.cursor.execute("Select id,nome,estado,tipo,cpu,n,mem from maq where tipo!='V'")
	todoshostsdb = db.cursor.fetchall()

	d = []
	for li in todoshostsdb:
		hostOK = False

		hostid = li["id"]

		print("\n\n*****\nHost: %s (%d)"%(li["nome"],hostid))
		db.cursor.execute("Select netdev.ip, netdev.rede, maq.altsec, maq.estado from maq,netdev where maq.id=netdev.maq AND maq.id='%d'"%hostid)
		hosts = db.cursor.fetchall()

		ipmi = ''
		li['redes'] = []
		# for iface in interfaces:
		for hostline in hosts:
			if hostline["rede"]=='ipmi':
				ipmi = hostline["ip"]
			else:
				li['redes'].append(hostline["ip"])

		if hostline["altsec"]:
			status = ipmiInfo(ipmi, hostline["altsec"])
			# print(ipmi, hostline["altsec"])
		else: status = ipmiInfo(ipmi)

		if hostline["estado"]!=status:
			print("Status ALTERADO %s %s"%(hostid,status))
			updcmd = "UPDATE maq SET estado='%s'	WHERE id='%s'"%(status,hostid)
			# print(updcmd)
			try:
				status = db.cursor.execute(updcmd)
			except:
				input("Erro atualização de status no BD >>"+updcmd)

			db.commit()

		if status!="1":
			continue
		# continue

		# for ip in li['redes']:
		# 	ret = hostinfo(ip,hostid)
		# 	if ret['STATUS']=="OK":
		# 		ipsucesso=ip
		# 		hostOK=True
		# 		break
		#
		# if not hostOK:
		# 	print("Problemas com host: ",li)
		# 	continue
		#
		# updcmd = """UPDATE maq SET cpu='%s', n=%d, mem='%s', kernel='%s', so='%s'
		# 		WHERE id='%s'
		# """%(ret["cpu"],ret["n"],ret["mem"],ret["kernel"],ret["so"],hostid)
		#
		# try:
		# 	status = db.cursor.execute(updcmd)
		# except:
		# 	print("Erro atualização de BD >>"+updcmd)
		# 	input("Pausado...")
		# db.commit()

		# selcmd = "SELECT * FROM maq WHERE hospedeiro='%s'"%hostid
		# db.cursor.execute(selcmd)
		# vms = db.cursor.fetchall()
		#
		# for vm in vms:
		# 	if vm["nome"] not in ret["all"]:
		# 		input("\t*** VM NOVA encontrada: %s %s"%(vm["nome"],vm["id"]))
		# 		# sql = "UPDATE maq SET estado='%s' WHERE id=%s"%(vm["estado"],vm["id"])
		# 		sql = """INSERT INTO maq (nome, estado, tipo, hospedeiro) VALUES ('%s','%s','%s','%s')
		# 			"""%(vm["nome"],vm["estado"],vm["tipo"],hostid)
		# 		db.cursor.execute(selcmd)
		# 		db.commit()
		#
		# 	if (vm["estado"]=='0' and vm["nome"] not in ret["off"] ) or \
		# 		(vm["estado"]=='1' and vm["nome"] not in ret["on"] ) or \
		# 		(vm["estado"]=='-1' and vm["nome"] not in ret["other"] ):
		# 		input("\t*** Estado alterado VM:  %s %s ( %s )"%(vm["nome"],vm["id"],vm["estado"]))
		#
		# 		sql = "UPDATE maq SET estado='%s' WHERE id=%s"%(vm["estado"],vm["id"])
		# 		db.cursor.execute(selcmd)
		# 		db.commit()
		#
		#
		# 	print("VM "+vm["nome"] + " Ok")


def ipmiInfo(ip,altsec=rootpw):
	print("\tIPMI "+ip)
	executa = ['ipmitool','-c', '-I','lanplus','-H', ip, '-U', 'admin', '-P', altsec,'power','status']
	output = subprocess.run(executa, capture_output=True, text=True	)
	if output.returncode==1:
		return "-1"
	else:
		mensagem = str(output.stdout).strip()
		ultima = mensagem.split()[-1]
		if str(ultima)=='on':
			return "1"
		else:
			return "0"

allHosts()
