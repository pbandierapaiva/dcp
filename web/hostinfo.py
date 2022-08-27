from browser import document
from browser import html, ajax, alert, confirm, prompt

from browser.widgets.dialog import InfoDialog, Dialog

# from rack import *
from utils import *

import json


# class HostList(html.DIV):
# 	def __init__(self, refreshState=False):
# 		html.DIV.__init__(self)
# 		ajax.get("/hosts", oncomplete=self.onLoadHosts)
# 		self.refreshState = refreshState
# 		self.className = "w3-sidebar w3-light-grey w3-bar-block"
# 		self.style={"width":"25%"}
# 		titulo = html.H3("Hosts")
# 		titulo.className = "w3-bar-item"
# 		self <= titulo

# 		vmButton = html.DIV("Lista VM Hosts", Class="w3-btn w3-block")
# 		vmButton.bind("click",self.vmlist)
# 		self <= vmButton
# 	def onLoadHosts(self, req):
# 		for h in req.json:
# 			self <= HostLine(h)
# 	def vmlist(self,ev):
# 		document["infoarea"].innerHTML=""
# 		document["infoarea"] <= VMHostList()
# class VMHostList(html.DIV):
# 	def __init__(self):
# 		html.DIV.__init__(self)
# 		Confirma("Certeza que deseja listar todos os hosts?", self.refresh)

# 	def refresh(self):
# 		ajax.get("/hosts", oncomplete=self.onLoadHosts)

# 	def onLoadHosts(self, req):
# 		for h in req.json:
# 			linhaHost = html.DIV()
# 			linhaHost.className = "w3-bar w3-block"
# 			self <= HostLine(h)  #html.P(h["nome"])

# 			if h["tipo"]!="H":
# 				next
# 			self <= EstadoVM(h)

class HostLine(html.DIV):
	def __init__(self, h, refreshState=False):
		html.DIV.__init__(self, Class= "w3-bar w3-block")
		self.cssBotao = "w3-button w3-tiny w3-center w3-padding-small w3-border w3-round"
		self.refreshState = refreshState
		self.hostdic = h
		self.bloqueia = None
		botaoHost = html.A(h["nome"])
		botaoHost.className = self.cssBotao
		botaoHost.style = {"width":"40%"}
		botaoHost.target = "infoarea"
		botaoHost.bind("click", self.maqinfo)
		botaoHost.hostid =h["id"] # "/hosts/"+str(h["id"])

		botContain = html.SPAN(Class= "w3-dropdown-hover")
		if h["tipo"]!='V':
			botaoIpmi = html.A("IPMI")
			botaoIpmi.className = self.cssBotao
			botaoIpmi.classList.add("w3-teal")
			botaoIpmi.target="_blank"
			for n in h["redes"]:
				if h["redes"][n] == "ipmi":
					botaoIpmi.href = "http://"+n
					break
			botContain <= botaoIpmi \
				<= html.DIV(Class="w3-dropdown-content w3-bar-block w3-border") \
				<= html.SPAN(n,Class="w3-bar-item w3-button")
		else:
			botaoIpmi = html.A("VM")
			botaoIpmi.className = self.cssBotao
			botaoIpmi.classList.add("w3-black")
			botaoIpmi.bind("click",self.hostinfo)
			botContain <= botaoIpmi \
				<= html.DIV(Class="w3-dropdown-content w3-bar-block w3-border") \
				<= html.SPAN(self.hostdic['hospedeiro'],Class="w3-bar-item w3-button")

		tagTipo=TipoHost(h, True)

		self.estadoHost = html.SPAN()
		self.estadoHost.innerHTML = "&nbsp;"
		self.estadoHost.className=self.cssBotao
		self.estadoHost.style = {"width":"3%"}
		if h["estado"]=="0": self.estadoHost.classList.add("w3-grey")
		elif h["estado"]=="1": self.estadoHost.classList.add("w3-green")
		else: self.estadoHost.classList.add("w3-yellow")

		self.estadoHost.bind("click",self.refrescastat)

		self <= botaoHost
		self <= botContain
		self <= tagTipo
		self <= self.estadoHost
	def refrescastat(self, ev):
		ajax.get("/hosts/"+str(self.hostdic["id"])+"/powerstatus",oncomplete=self.updatestatus)
		self.bloqueia = Alerta("Aguarde a conexão com o Host")
		self.estadoHost.className=self.cssBotao
		self.estadoHost.classList.add("w3-yellow")
	def updatestatus(self,res):
		d = res.json
		if d["STATUS"]=="ERRO":
			self.bloqueia.setmsg(d["msg"])
			self.estadoHost.className=self.cssBotao
			self.estadoHost.classList.add("w3-red")
			return
		if d["power"] == "0":
			estadoText = "Desligado"
		else:
			estadoText = "Ligado"

		if d["power"]!=self.hostdic["estado"]:
			self.bloqueia.setmsg("Alterando status para: "+estadoText)
			ajax.put("/hosts/%s/powerstatus/%s"%(self.hostdic["id"],d["power"]))
			return
		else:
			self.bloqueia.dismiss(0)
			# self.bloqueia.setmsg("Estado já atualizado")
		self.estadoHost.className=self.cssBotao
		if d["power"] == "1":
			self.estadoHost.classList.add("w3-green")
		else:
			self.estadoHost.classList.add("w3-grey")
	def maqinfo(self, ev):
		# NodeInfo(ev.currentTarget.hostid)
		NodeInfo(self.hostdic['id'])
	def hostinfo(self, ev):
		# NodeInfo(ev.currentTarget.hostid)
		NodeInfo(self.hostdic['hospedeiro'])
	def vmstate(self,ev):
		document["infoarea"].innerHTML=""
		document["infoarea"] <= EstadoVM(ev.currentTarget.hostinfo)

class NodeInfo(html.DIV):
	def __init__(self, h):
		html.DIV.__init__(self)
		document["infoarea"].innerHTML=""
		document["infoarea"] <= self
		if type(h)==int:
			ajax.get("/hosts/"+str(h), oncomplete=self.onLoadInfo)
			self.clear()
		else:
			Alerta("Esse objeto não suporta mais não inteiros")
	# 	if type(h)==int:
	# 		self.hostid = h
	# 		self.loc = "/hosts/"+str(h)
	# 		self.carrega()
	# 	else:
	# 		self.hostid = h["id"]
	# 		self.loc = "/hosts/"+str(h["id"])
	# 		self.onLoadInfo(h)
	# def carrega(self):
	# 	ajax.get(self.loc, oncomplete=self.onLoadInfo)
	# 	self.clear()
	def onLoadInfo(self, req):
		# if type(req)==dict:
		# 	self.dadoshost=req
		# else:
			# self.dadoshost = req.json

		#
		# tit = document["hititle"]
		# tit.innerHTML = "Host info: "+self.dadoshost["nome"]
		self.dadoshost = req.json
		form = html.FORM()
		form.className = "w3-container"
		titulo = html.LABEL("<h2>ID: "+str(self.dadoshost["id"])+" - "+self.dadoshost["nome"]+"</n2>")
		form <= titulo
		form <= HostLine(self.dadoshost)
		self.nome = EntraTexto("Nome",self.dadoshost["nome"])
		form <= self.nome
		self.comentario = EntraTexto("Comentário",self.dadoshost["comentario"])
		form <= self.comentario
		self.cposo = EntraTexto("Sistema operacional",self.dadoshost["so"])
		form <= self.cposo
		self.kernel = EntraTexto("Kernel",self.dadoshost["kernel"])
		form <= self.kernel
		self.cpu = EntraTexto("Processador",self.dadoshost["cpu"]) #, width="70%")
		self.n = EntraTexto("N",self.dadoshost["n"]) #, width="30%")
		self.mem = EntraTexto("Memória",self.dadoshost["mem"])  #, width="30%")
		cpulinha = html.TR()
		cpulinha <= html.TD(style={"width":"60%"}) <= self.cpu
		cpulinha <= html.TD(style={"width":"10%"}) <= self.n
		cpulinha <= html.TD(style={"width":"20%"}) <= self.mem
		form <= html.TABLE() <= cpulinha
		self.tipo = TipoHost(self.dadoshost)
		self.estado = RadioEstado(self.dadoshost["estado"])

		self.listaInt = ListaInterfaces( self ) # campos ) #self.loc, campos["redes"] )

		linhaEstadoTipo = html.DIV(Class = "w3-cell-row")
		linhaEstadoTipo <= html.DIV(html.LABEL("<p>Estado</p>"),Class = "w3-cell")
		linhaEstadoTipo <= html.DIV(Class = "w3-cell") <= self.estado
		linhaEstadoTipo <=  html.DIV(Class = "w3-cell") <= self.tipo
		linhaEstadoTipo <=  html.DIV(Class = "w3-cell") <= self.listaInt

		form <= linhaEstadoTipo

		self.editBtn = html.DIV("Editar")
		self.editBtn.className = "w3-button w3-border w3-margin"
		self.editBtn.unbind("click")
		self.editBtn.bind("click", self.editar)
		self.editBtn.style = {"display":"block"}
		self.cancelBtn = html.DIV("Cancelar")
		self.cancelBtn.className = "w3-button w3-border w3-margin"
		self.cancelBtn.bind("click", self.cancelar)
		self.cancelBtn.style = {"display":"none"}
		form.append(self.editBtn)
		form.append(self.cancelBtn)

		self.appendChild(form)
		if self.dadoshost["tipo"]=="H":
			self <= html.H3("Máquinas virtuais")
			self.appendChild(EstadoVM(self.dadoshost))
	def editar(self, ev):
		self.nome.enable()
		self.comentario.enable()
		self.cposo.enable()
		self.kernel.enable()
		self.cpu.enable()
		self.n.enable()
		self.mem.enable()

		self.estado.enable()
		# self.tipo.disabled = False
		self.tipo.enableEdit()
		self.listaInt.enableEdit()

		self.editBtn.innerHTML = "Salvar"
		self.editBtn.unbind("click")
		self.editBtn.bind("click", self.salvar)
		self.cancelBtn.style = {"display":"block"}
	def alterado(self):
		return self.nome.alterado or self.comentario.alterado or self.cposo.alterado or self.kernel.alterado or self.cpu.alterado or self.n.alterado or \
			self.mem.alterado or self.estado.alterado
	def salvar(self, ev):
		if not self.alterado():
			Alerta("Dados inalterados","Informações de nó")
			self.carrega()
			return
		dados = {"hostid": self.hostid,
				"nome" :  self.nome.valor(),
				"comentario" : self.comentario.valor(),
				"so" : self.cposo.valor(),
				"estado" : self.estado.valor(),
				"tipo" : self.tipo.valor(),
				"kernel" : self.kernel.valor(),
				"cpu" : self.cpu.valor()
				}
		try:
				if	self.n.valor(): dados["n"] = int(self.n.valor())
				if	self.mem.valor(): dados["mem"] = int(self.mem.valor())
		except:
				Alerta("Valores de N e MEM devem ser inteiros", "Erro")
				return
		ajax.post("/hosts/%d"%self.hostid, data=json.dumps(dados), oncomplete=self.added, headers={"Content-Type": "application/json; charset=utf-8"})
	def added(self,req):
		if req.json["STATUS"]!="OK":
			Alerta("Erro de atualização de Host","Erro")
		self.carrega()
	def cancelar(self, ev):
		if self.alterado():
			if confirm("Descartar alterações?"):
				self.carrega()
		else:
			self.carrega()

class NodeInfoLine(html.DIV):
	def __init__(self, hinfodic):
		html.DIV.__init__(self, Class="w3-card w3-margin") #, style={"width":"40%"})
		self.hinfo = hinfodic
		base = html.DIV(Class="w3-bar")
		base <=html.DIV( self.hinfo['id'], Class="w3-bar-item")
		base <=html.DIV( self.hinfo['nome'], Class="w3-bar-item")
		bot  = html.DIV("&nbsp;", Class="w3-bar-item")
		bot.className="w3-badge w3-tiny w3-right w3-margin"
		if hinfodic['estado']=='1':
			bot.classList.add("w3-green")
		elif hinfodic['estado']=='0':
			bot.classList.add("w3-grey")
		else:
			bot.classList.add("w3-yellow")
		base <= bot
		self <= base 

class EstadoVM(html.DIV):
	def __init__(self, hostinfo):
		html.DIV.__init__(self, Class="w3-container w3-margin")
		self.hostid = hostinfo["id"]
		self.ip = ""
		self.ips = []
		for n in hostinfo["redes"]:
			if hostinfo["redes"][n] != "ipmi":
				self.ip = n
				self.ips.append(n)

		anc = html.SPAN(hostinfo["nome"]+"("+str(hostinfo["id"])+")", Class="w3-ripple")
		anc.bind("click",self.homeHost)
		tit = html.DIV()
		tit.innerHTML = "VMs on host: "
		tit <= anc
		self.refresh()
	def homeHost(self,ev):
		document["infoarea"].innerHTML=""
		document["infoarea"] <= NodeInfo(self.hostid)
	def refresh(self):
		self.innerHTML=""
		ajax.get("/hosts/%s/vm"%self.hostid, oncomplete=self.onLoadRegisteredVMs)
	def onLoadRegisteredVMs(self,res):
		self.vms = res.json
		for vm in self.vms:
			if vm["estado"]=='1':
				self <= NodeInfoLine(vm)
		for vm in self.vms:
			if vm["estado"]!='1':
				self <= NodeInfoLine(vm)
		self.rev = html.DIV(Class="w3-container w3-margin w3-ripple")
		self.rev <= 	html.I(Class="fa fa-refresh")
		self.rev.bind("click",self.refreshHostVMs)
		self <= self.rev
	def refreshHostVMs(self, req):
		Confirma("Conectar ao servidor para informações de VMs?", self.confirmaLoadedHostVMs)
	def confirmaLoadedHostVMs(self):
		self.rev.className="fa fa-hourglass"
		self.sucessoLVMs = False
		if len(self.ips)<=0:
			Alerta("IP não cadastrado","Erro")
			return
		for ip in self.ips:
			Alerta("Checando IP: "+ip)
			ajax.get("/vmhosts/%s"%ip, oncomplete=self.loadedHostVMs)
	def loadedHostVMs(self, req):
		vmstatus = req.json
		if vmstatus["STATUS"] != "OK":
			Alerta("ERRO: " + vmstatus["MSG"],"Erro")
			return
		self.sucessoLVMs = True
		liall = set( vmstatus["all"])
		lirvmall= []
		for vmreg in self.vms:
			lirvmall.append(vmreg["nome"])
		rvmall = set(lirvmall)

		if (rvmall - liall):
			Alerta(	"Registradas e não definidos "+str(rvmall - liall ))

		for rvm in self.vms:
			if rvm["estado"]!="1" and rvm["nome"] in vmstatus["on"]:
					ajax.post("/hosts/%s/status/on"%(rvm["id"]), oncomplete=self.statusChangeResult)
			if rvm["estado"]!="0" and rvm["nome"] in vmstatus["off"]:
					ajax.post("/hosts/%s/status/off"%(rvm["id"]), oncomplete=self.statusChangeResult)
			if rvm["estado"]!="-1" and rvm["nome"] in vmstatus["other"]:
					ajax.post("/hosts/%s/status/other"%(rvm["id"]), oncomplete=self.statusChangeResult)

		adefinir = liall - rvmall
		for n in adefinir: # máquinas definidas nos servidores mas não no BD
			d = {"nome":n, "tipo":"V", "hospedeiro":self.hostid}
			if n in vmstatus["on"]: d["estado"]="1"
			elif n in vmstatus["off"]: d["estado"]="0"
			else: d["estado"]="-1"
			ajax.put("/vm/", data=json.dumps(d), oncomplete=self.vmAdded, headers={"Content-Type": "application/json; charset=utf-8"})

		self.refresh()
	def statusChangeResult(self, res):
		Alerta(res.json)
		self.refresh()


	def vmLoaded(self,req):
		vm = req.json["vm"]
		if not req.json["STATUS"]:
			# alert("VM não encontrada, criando entrada no DB")
			d = {"nome":vm, "tipo":"V", "hospedeiro":self.hostid}
			if vm in self.estado["on"]: d["estado"]="1"
			elif vm in self.estado["off"]: d["estado"]="0"
			else: d["estado"]="-1"
			ajax.put("/vm/", data=json.dumps(d), oncomplete=self.vmAdded, headers={"Content-Type": "application/json; charset=utf-8"})
	def vmAdded(self, req):
		if not 'STATUS' in req.json:
			Alerta(str(req.json))
			return
		if req.json["STATUS"]!="OK":
			Alerta(req.json["STATUS"])

class TipoHost(html.DIV):
	def __init__(self, h, mini=False):
		html.DIV.__init__(self)
		if mini:
			self.style = {"width":"10%"}
			self.classList = "w3-button w3-tiny w3-center w3-padding-small w3-border w3-round"
		else:
			self.classList = "w3-tag w3-margin w3-padding w3-dropdown-hover"
			self.style = {"width":"200px"}
		self.disabled = True
		self.hostinfo = h
		self.tipo = h["tipo"]
		if self.tipo=="H":  # HOST
			if mini:self.innerHTML = "H"
			else: self.innerHTML = "Host"
			if self.hostinfo["estado"]=='1':
				self.classList.add("w3-blue")
			else: self.classList.add("w3-grey")
			# self.bind("click",self.vmstate)
		elif self.tipo=="S":  # Standalone
			if mini:self.innerHTML = "S"
			else:self.innerHTML = "Standalone"
			self.classList.add("w3-cyan")
		elif self.tipo=="V":  # Máq. virtual
			if mini:self.innerHTML = "V"
			else:self.innerHTML = "VM"
			self.classList.add("w3-blue-grey")
		else:  # Desconhecido
			if mini:self.innerHTML = "??"
			else:self.innerHTML = "desconhecido"
			self.classList.add("w3-grey")
		if not mini:
			setH = html.A(Class="w3-bar-item w3-button")
			setH.innerHTML="Host"
			setH.bind("click", self.seth)

			setS = html.A(Class="w3-bar-item w3-button")
			setS.innerHTML="Standalone"
			setS.bind("click", self.sets)
			dropdownitems = html.DIV(Class="w3-dropdown-content w3-bar-block w3-card-4")
			dropdownitems <= setH
			dropdownitems <= setS
			self <= dropdownitems
			self.style = {"pointer-events": "none"}
	def sets(self, ev):
		ajax.post("/hosts/%s/tipo/S"%self.hostinfo["id"])
	def seth(self, ev):
		ajax.post("/hosts/%s/tipo/H"%self.hostinfo["id"])
	def valor(self):
		return self.tipo
	def enableEdit(self):
		self.style = {"pointer-events": "auto"}

class ListaInterfaces(html.DIV):
	def __init__(self, hostnode):     #loc, h):
		html.DIV.__init__(self)
		self.interfaces = hostnode.dadoshost["redes"]
		self.hid =  hostnode.dadoshost["id"]
		self.loc = "/hosts/"+str(hostnode.dadoshost["id"])
		self.hostnode = hostnode
		# carrega cores das redes
		ajax.get("/nets/", oncomplete=self.onLoadNets)
	def onLoadNets(self,req):
		redesCores = req.json
		dredesCor={}
		for r in redesCores:
			dredesCor[r["nome"]] = r["cor"]
		self.ifaceTags = []
		self.ifaceDdowns = []
		for ip in self.interfaces:
			if self.interfaces[ip]=="ipmi":
				continue
			# self <= html.BR()
			tag = html.BUTTON(Class = "w3-button")
			#tag.classList =  # w3-tag"
			tag.style ={"width":"200px"}   #,"cursor":"default"}
			tag.innerHTML = ip
			tag.classList.add(dredesCor[  self.interfaces[ip]  ])

			tag.bind("click", self.clickIP)

			delif = html.A(Class="w3-bar-item w3-button")
			delif.innerHTML="Remover interface"
			delif.ip = ip
			delif.bind("click", self.netdevRemove)

			release = html.A(Class="w3-bar-item w3-button")
			release.innerHTML="Dist release"
			release.ip = ip
			release.bind("click", self.getRelease)

			dropdown =  html.DIV(Class="w3-dropdown-hover")
			dropdown <= tag
			dropdownitems = html.DIV(Class="w3-dropdown-content w3-bar-block w3-card-4")
			dropdownitems <= delif
			# dropdownitems <= uname
			dropdownitems <= release
			dropdown <= dropdownitems
			dropdown.style = {"pointer-events": "none"}

			self <= dropdown
			self.ifaceTags.append(tag)
			self.ifaceDdowns.append(dropdown)
	def clickIP(self,ev):
		alert(ev.currentTarget.innerHTML)

	def novoNetDev(self, ev):
		AddNet(self.loc)
	def enableEdit(self):
		novoDev = html.DIV("+")
		novoDev.bind("click", self.novoNetDev )
		novoDev.className = "w3-tag w3-white"
		novoDev.style = {"display":"block", "width":"120px","cursor":"pointer"}
		self <= novoDev
		for iDd in self.ifaceDdowns:
			iDd.style = {"pointer-events": "auto"}

	def netdevRemove(self, ev):
		self.ip = ev.currentTarget.ip
		Confirma("ATENÇÃO: Remover interface "+self.ip+ "?", self.netdevRemoveConfirm)
	def netdevRemoveConfirm(self):
		ajax.delete("/netdev/%s"%self.ip, oncomplete=self.netdevRemovedOK)
	def netdevRemovedOK(self, ev):
		NodeInfo(self.hid)
	def getRelease(self,ev):
		ajax.get("/vmhosts/%s/release"%ev.currentTarget.ip, oncomplete=self.dispRelease)
	def dispRelease(self,req):
		if req.json["STATUS"]!="":
			Alerta(req.json["STATUS"])
		self.hostnode.kernel.setavalor(req.json["kernel"])
		self.hostnode.kernel.classList.add( "w3-border")
		self.hostnode.kernel.classList.add( "w3-border-red")

		self.hostnode.cposo.setavalor(req.json["so"])
		self.hostnode.n.setavalor(req.json["n"])
		self.hostnode.cpu.setavalor(req.json["proc"])
		self.hostnode.mem.setavalor(req.json["mem"])


		if req.json["error"]=="":
			Alerta(req.json["out"].strip())
		else: Alerta(req.json["error"])

class AddNet(html.DIV):
	def __init__(self,loc):
		html.DIV.__init__(self)
		self.loc = loc + "/net"
		self.maq = int(loc.split("/")[-1])
		document["dialog"] <= self
		self.className = "w3-modal"
		self.style.display = "block"  #"none"
		continente = html.DIV()
		continente.className = "w3-modal-content"
		caixa =  html.DIV()
		caixa.className = "w3-container w3-padding"
		fechaCaixa = html.SPAN("&times")
		fechaCaixa.className="w3-button w3-display-topright"
		fechaCaixa.bind("click", self.fecha)
		caixa <= html.H3("Adicionando interface de rede")
		caixa <= fechaCaixa
		caixa <= html.LABEL("Rede")
		self.rede=SelectNet()
		caixa <= self.rede
		caixa <= html.LABEL("Endereço IP")
		self.ip = html.INPUT()
		self.ip.className = "w3-input w3-border"
		caixa <= self.ip

		caixa <= html.LABEL("Ethernet")
		self.ether = html.INPUT()
		self.ether.className = "w3-input w3-border"
		caixa <= self.ether
		ok = html.BUTTON("OK")
		ok.className = "w3-button w3-margin w3-border w3-round"
		ok.bind("click", self.confirma)

		caixa <= ok
		continente <= caixa
		self <=continente
	def confirma(self,ev):
		self.style.display = "none"
		d = {"ip":self.ip.value, "rede":self.rede.selecionado(),
			"maq":self.maq, "ether":self.ether.value }
		ajax.put("/netdev", data=json.dumps(d), oncomplete=self.added, headers={"Content-Type": "application/json; charset=utf-8"})
	def added(self, req):
		if req.json["STATUS"]=="OK":
			Alerta("Interface adicionada","Rede")
		else:
			Alerta(req.json["STATUS"])
		NodeInfo(self.maq)
	def show(self):
		self.style.display = "block"
	def fecha(self, ev):
		self.style.display = "none"

class SelectNet(html.SELECT):
	def __init__(self):
		html.SELECT.__init__(self)
		self.className = "w3-input w3-border"
		ajax.get("/nets/", oncomplete=self.onLoadNets)
	def onLoadNets(self,req):
		redes = req.json
		for r in redes:
			self <= html.OPTION(r["nome"]+" - "+ r["cidr"], value=r["nome"]	)
	def selecionado(self):
		return self.selectedOptions.item(0).value

class Busca(html.DIV):
	def __init__(self):
		html.DIV.__init__(self)
		PegaTexto("Nome do nó", self.buscaNome)
	def buscaNome(self, nome):
		if nome=="":
			return
		ajax.get("/busca/%s"%nome, oncomplete=self.retBusca)
	def retBusca(self,res):
		document["infoarea"].innerHTML=""
		if not len( res.json ):
			Alerta("Não encontrado")
		else:
			for h in  res.json:
			 	self <= HostLine(h)
			document["infoarea"]<=self

def buscaNo(ev):
	Busca()
