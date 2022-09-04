#!bin/python
#
# Conecta em todas as máquinas físicas marcadas como Host e resgata seus estados
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
	# verifica status (ON/OFF) somente Hosts que não são VMs 'V'
	# db.cursor.execute("Select id,nome,estado,tipo,cpu,n,mem from maq where tipo!='V'")
	db = DB()

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
