from browser import document, window
from browser import html, ajax, alert, confirm, prompt

from browser.widgets.dialog import InfoDialog, Dialog

from utils import *

import json

class Cabecalho(html.DIV):
    def __init__(self, updateHook):
        html.DIV.__init__(self, Class="w3-bar w3-card-2 w3-blue notranslate")
        self.innerHTML = "DCP-DIS-EPM-Unifesp"
        self.autenticado=None
        self.botaoAuth = html.BUTTON("Autentica",Class="w3-btn w3-grey w3-round w3-margin-left ")
        self.botaoAuth.bind("click", self.pedeCredencial)
        self <= self.botaoAuth
        self.statusData = html.SPAN()
        self <= self.statusData
        self.updateHook = updateHook
        self.update()
    def update(self):
        if not self.autenticado:
            self.botaoAuth.innerHTML = "Autentica"
        else:
            self.botaoAuth.innerHTML = "Logout"
        ajax.get("/DC", oncomplete=self.dataLoaded)
    def dataLoaded(self, res):
        medias = res.json 
        self.statusData.innerHTML=""
        for lin in medias:
            self.statusData <= html.SPAN( "  %s : %4.2f | ON %s / OFF %s "%(lin["DC"], lin['avg_temp'], lin['stateON'], lin['stateOFF']),
                                        Class="w3-right w3-margin-left w3-margin-right")
        self.updateHook()
    def pedeCredencial(self, evt):
        if not self.autenticado:
            PegaTexto("Autentica", self.confirmaCredencial)
        else:
            self.autenticado=None
            self.update()
    def confirmaCredencial(self, resposta):
        self.autenticado=resposta
        self.update()
    




class GridServidores(html.DIV):
    def __init__(self):
        html.DIV.__init__(self) 
        self.cabeca = Cabecalho(self.loadServerData)
        self.dcDIS = html.DIV(Class="w3-row w3-topbar w3-bottombar w3-border-blue w3-pale-blue")
        self.dcSTI = html.DIV(Class="w3-row w3-topbar w3-bottombar w3-border-blue w3-pale-blue")
        self <= self.cabeca
        self <= self.dcSTI
        self <= self.dcDIS 
        self.servidores = []
        self.loadServerData()
    def loadServerData(self):
        self.servidores = []
        self.dcSTI.innerHTML=""
        self.dcDIS.innerHTML=""
        if self.cabeca.autenticado is None:
            senha = ""
        else:
            senha = self.cabeca.autenticado
        # alert(self.cabeca.autenticado)
        dados = {'password': senha} #self.cabeca.autenticado}
        ajax.post("/hosts", data=json.dumps(dados), oncomplete=self.dataLoaded,
            headers={"Content-Type":"application/json"})
        # ajax.post("/hosts", data=json.dumps(dados), oncomplete=self.dataLoaded)
    def dataLoaded(self, res):
        hostlist = res.json
        for item in hostlist:
            serv =  CaixaServidor(item, self.cabeca.autenticado)
            self.servidores.append(serv)
            if item["DC"]=="DIS":
                self.dcDIS <= serv
            else:
                self.dcSTI <= serv
    def update(self):
        for s in self.servidores:
            s.update()

class CaixaServidor(html.DIV):
    def __init__(self, data, autentica=None):
        html.DIV.__init__(self,Class="w3-col m3 w3-round w3-border")                   # "w3-card-4 server-box")
        self.id = data["id"]
        self.nome = data["Nome"]
        self.ipmi = data["IPMI_IP"]
        if "senhaIPMI" in data:
            self.pwipmi = data["senhaIPMI"]
        else:
            self.pwipmi = None
        self.hostip = data["HostIP"]
        self.usrip = data["IP_USER"]
        self.dc = data["DC"]
        self.tipo = data["H_S_X"]
        self.desc = data["Descricao"]
        self.temp = data["temp"]
        self.status = data["state"]

        # Header
        cabeca = html.HEADER( Class="w3-container w3-row w3-padding w3-dark-grey")

        texto = html.SPAN(f"{self.id} - {self.nome}",title=self.desc, 
            Class="w3-left")
        
        if autentica:
            hardOff = html.I("do_not_disturb", 
                Class="w3-right material-icons w3-hover-pointer", 
                style="color:red", title="HARD OFF")
            hardOff.bind("click", self.confirmaHardOFF)
            alteraEstado = html.I("power_settings_new", 
                Class="w3-right material-icons w3-hover-pointer", 
                style="color:white")
            alteraEstado.bind("click", self.confirmSoftOnOff)
            cabeca <= hardOff
            cabeca <= alteraEstado
        cabeca <= texto
        self <= cabeca

        corcaixa=""
        if self.status:   # ON
            if (self.temp) and self.temp>35:
                corcaixa="w3-light-red"
            else:
                corcaixa="w3-light-green"
        else:
            if self.status is None:
                corcaixa="w3-white"
            else: # OFF
                corcaixa="w3-light-grey"
        self.classList.add(corcaixa)

        grid_container = html.DIV(Class="w3-row-padding w3-padding")
        area1 = html.DIV(botaoLink("IPMI", f"http://{self.ipmi}"), Class=f"w3-col s4  w3-padding")
        area2 = html.DIV(f"Type: {self.tipo}", Class=f"w3-col s4  w3-padding")
        area3 = html.DIV( "---", Class=f"w3-col s4  w3-padding")
        if self.temp:
            area3.innerHTML = f"{self.temp}°C"
        grid_container <= area1
        grid_container <= area2
        grid_container <= area3
        self <= grid_container
    def confirmaHardOFF(self, evt):		
        Confirma("DESLIGAR - HARD OFF "+self.nome+ "?", self.hardOFF)
    def hardOFF(self):
        alert("HARD OFF")
    def confirmSoftOnOff(self, evt):
        if self.status:
            Confirma("Confirma SOFT OFF?", self.softOff)
        else:
            Confirma("Confirma ON?", self.powerON)
    def softOff(self):
        alert("SOFT")
    def powerON(self):
        alert("ON")

class botaoLink(html.BUTTON):
    def __init__(self, texto, url):
        html.BUTTON.__init__(self,Class="w3-round w3-border") 
        self.innerHTML = texto
        self.link = url
        self.bind("click", self.abreJanela)
    def abreJanela(self,evt):
        window.open(self.link, "_blank")

class Principal(html.DIV):
    def __init__(self):
        html.DIV.__init__(self)
        self.grade = GridServidores()
        self <= self.grade


document <= Principal()
# document <= Cabecalho()
# document <= GridServidores()
    
