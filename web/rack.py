from browser import document
from browser import html, ajax, alert, confirm

from hostinfo import NodeInfo

UHEIGHT = 25
RWIDTH = "200px"
RHEIGHT = "2500px"

class InfoArea( html.DIV ):
	def __init__(self):
		html.DIV.__init__(self, id="infoarea",  Class="w3-container", style={"margin-left":RWIDTH})

class Rack( html.DIV ):
	def __init__(self):
		html.DIV.__init__(self, Class="w3-sidebar w3-grey w3-bar-block")   #"w3-sidenav w3-grey") # w3-card-2")
		self.style = {"width": RWIDTH, "margin":0, "padding":0} #, "height":"100%", "position":"absolute"}
		self.hd={}
		#rack.style={"display": "table-cell"}
		ajax.get("/hosts", oncomplete=self.dataLoaded)
	def dataLoaded(self, res):
		hostlist = res.json
		for item in hostlist:
			self.hd[item["id"]]=Servidor(item)     #item
		self.carregaUnidades()
	def carregaUnidades(self):
		self <= Unidade(1, "Dataceter-Unifesp")
		self <= Unidade(2,[self.hd[558],self.hd[559],self.hd[560],self.hd[561]])
		self <= Unidade(1, "DCP-DIS-Unifesp")
		self <= Unidade(1, "RACK 1")
		self <= Unidade(1, [self.hd[525]])
		self <= Unidade(1, [self.hd[524]])
		self <= Unidade(1, [self.hd[523]])
		self <= Unidade(1, [self.hd[522]])
		self <= Unidade(1, [self.hd[521]])
		self <= Unidade(1, [self.hd[567]])
		self <= Unidade(1, "DISPLAY")
		self <= Unidade(2, [self.hd[563]])
		self <= Unidade(2, [self.hd[562]])
		self <= Unidade(1, "Aruba-237")
		self <= Unidade(1, "Aruba-236")
		self <= Unidade(2,[self.hd[554],self.hd[555],self.hd[556],self.hd[557]])
		self <= Unidade(2,[self.hd[550],self.hd[551],self.hd[552],self.hd[553]])
		self <= Unidade(2,[self.hd[546],self.hd[547],self.hd[548],self.hd[549]])
		self <= Unidade(2,[self.hd[542],self.hd[543],self.hd[544],self.hd[545]])
		self <= Unidade(2,[self.hd[538],self.hd[539],self.hd[540],self.hd[541]])
		self <= Unidade(2,[self.hd[534],self.hd[535],self.hd[536],self.hd[537]])
		self <= Unidade(2,[self.hd[530],self.hd[531],self.hd[532],self.hd[533]])
		self <= Unidade(2,[self.hd[526],self.hd[527],self.hd[528],self.hd[529]])
		self <= Unidade(1, "RACK 2")
		self <= Unidade(1, [self.hd[565]])
		self <= Unidade(1, [self.hd[567]])
		self <= Unidade(2, [self.hd[566]])

class Unidade(html.DIV ):
    def __init__(self, h, mods):
        html.DIV.__init__(self, Class="w3-bar-item w3-button")  #"w3-container w3-row")
        self.classList.add("w3-border")
        self.style = { "height":"100%", "width": "100%", "margin":0, "padding":0}

        self.mods = mods
        self.style = { "height":"%dpx"%(UHEIGHT*h), "width": RWIDTH}

        if type(mods)==str:
            self<= Modulo(mods)
        elif len(self.mods)==1:    
            self<=  self.mods[0]
        elif len(self.mods)==4:
            cel1 = html.DIV(Class="w3-half")
            cel2 = html.DIV(Class="w3-half")
            cel1.style={"height":"50%"}
            cel2.style={"height":"50%"}
            cel1 <= self.mods[1]
            cel1 <= self.mods[0]
            cel2 <= self.mods[3]
            cel2 <= self.mods[2]
            self <= cel1
            self <= cel2

# class Modulo(html.DIV):
# 	def __init__(self, hinfo=None):
# 		html.DIV.__init__(self)  #, Class="w3-panel w3-cell w3-red")
# 		self.classList.add("w3-border")
# 		self.classList.add("w3-tiny")
# 		self.style = { "margin":0, "padding":0, "height":"100%"}#,   "height": "100vh"}
# 		self.h = hinfo
# 		if type(hinfo)==str:
# 			self.innerHTML=hinfo
# 			self.classList.add("w3-light-grey")
# 		elif self.h!=None:
# 			self.id = "mod-%d"%self.h.id
# 			self.refresh()
# 	def refresh(self):
# 		self.innerHTML = str(self.h.id) + " - " + self.h.nome
# 		self.classList.add("w3-hover-blue")
# 		# if self.h["estado"][0]=='1':
# 		# 	if self.h["tipo"][0]=='H':
# 		# 		self.classList.add("w3-blue")
# 		# 	else:
# 		# 		self.classList.add("w3-cyan")
# 		# elif  self.h["estado"][0]=='-1':
# 		#     self.classList.add("w3-yellow")
# 		self.bind("click", self.mostraHost)
# 	def mostraHost(self,ev):
# 		NodeInfo(self.h.id)

class Servidor(html.DIV):
	def __init__(self, d):
		html.DIV.__init__(self)

		self.id = int( d["id"] )
		self.nome = d["Nome"]
		self.ipmiip = d["IPMI_IP"]
		self.senhaipmi = d["senhaIPMI"]
		self.hostip = d["HostIP"]
		self.hsx = d["H_S_X"]
		self.desc = d["Descricao"]
		self.estado = 'X'
		self.temp=None

		self.classList.add("w3-border")
		self.classList.add("w3-tiny")
		self.style = { "margin":0, "padding":0, "height":"100%"}
		self.innerHTML = str(self.id) + " - " + self.nome
		self.classList.add("w3-hover-blue")
		self.bind("click", self.mostraHost)
		self.refresh()
	def refresh(self):
		ajax.get("/hosts/%d/status"%self.id, oncomplete=self.dataLoaded)
	def dataLoaded(self,res):
		hostinfo = res.json
		self.temp=hostinfo["temp"]
		if hostinfo["power"]:
			self.estado = '1'
			if self.temp>30:
				self.classList.add("w3-blue")
			else:
				self.classList.add("w3-red")
		else:
			self.estado = '0'
			self.classList.add("w3-cyan")
	def mostraHost(self,ev):
		NodeInfo(self.id)
