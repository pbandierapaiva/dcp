from browser import document, window
from browser import html, ajax, alert, confirm, prompt

from browser.widgets.dialog import InfoDialog, Dialog

from utils import *

import json

class Cabecalho(html.DIV):
    def __init__(self, updateHook):
        html.DIV.__init__(self, Class="w3-bar w3-card-2 w3-blue notranslate")
        self.innerHTML = "DCP-DIS-EPM-Unifesp"
        self.updateHook = updateHook
        self.autenticado=""
        self.mode="grid"
        
        self.userIcon= self.userIcon = html.I("no_accounts", 
                Class="material-icons w3-hover-pointer w3-right", 
                style="color:white")
        self.userIcon.bind("click", self.pedeCredencial)
        self <= self.userIcon

        self.grafViewIcon = html.I("ssid_chart", 
                Class="material-icons w3-hover-pointer w3-right", 
                style="color:white")
        self.grafViewIcon.bind("click", self.setModeTemp)   
        self <= self.grafViewIcon

        self.gridViewIcon = html.I("grid_on", 
                Class="material-icons w3-hover-pointer w3-right", 
                style="color:white")
        self.gridViewIcon.bind("click", self.setModeGrid)   
        self <= self.gridViewIcon
        
        self.statusData = html.SPAN()
        self <= self.statusData
        self.update()
    def setModeTemp(self, evt):
        self.mode="temp"
        self.updateHook()
    def setModeGrid(self, evt):
        self.mode="grid"
        self.updateHook()
    def update(self):
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
            self.autenticado=""
            self.confirmaCredencial("")
            self.update()
    def confirmaCredencial(self, resposta):
        self.autenticado=resposta
        if self.autenticado=="":
            self.userIcon.innerHTML=""
            self.userIcon <= html.I("no_accounts", 
                Class="material-icons w3-hover-pointer w3-right", 
                style="color:white")
        else:
            self.userIcon.innerHTML=""
            self.userIcon <= html.I("person", 
                Class="material-icons w3-hover-pointer w3-right", 
                style="color:white")
        self.update()

class GridServidores(html.DIV):
    def __init__(self, cabeca):
        html.DIV.__init__(self) 
        self.cabeca = cabeca
        self.dcDIS = html.DIV(Class="w3-row w3-topbar w3-bottombar w3-border-blue w3-pale-blue")
        self.dcSTI = html.DIV(Class="w3-row w3-topbar w3-bottombar w3-border-blue w3-pale-blue")
        self <= self.dcSTI
        self <= self.dcDIS 
        self.loadServerData()
    def loadServerData(self):
        self.servidores = []
        self.dcSTI.innerHTML=""
        self.dcDIS.innerHTML=""
        ajax.post("/hosts", 
            data=json.dumps({'password':self.cabeca.autenticado}), 
            oncomplete=self.dataLoaded,
            headers={"Content-Type":"application/json"})
    def dataLoaded(self, res):
        resposta = res.json
        if self.cabeca.autenticado!="" and not resposta["Autenticado"]: #senha errada
            self.cabeca.confirmaCredencial("")
        for item in resposta["result"]:
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
        html.DIV.__init__(self,Class="w3-col m2 w3-round w3-border")
        self.autentica = autentica
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
        self.updateAparencia()
    def updateAparencia(self):
        self.innerHTML=""
        # Header
        cabeca = html.HEADER( Class="w3-container w3-row w3-dark-grey")
        texto = html.SPAN(f"{self.id} - {self.nome}",title=self.desc, 
            Class="w3-left")    
        
        if self.autentica:
            self.hardOff = html.I("do_not_disturb", 
                Class="w3-right material-icons w3-hover-pointer", 
                style="color:red", title="HARD OFF")
            self.hardOff.bind("click", self.confirmaHardOFF)
            self.alteraEstado = html.I("power_settings_new", 
                Class="w3-right material-icons w3-hover-pointer", 
                style="color:white")
            self.alteraEstado.bind("click", self.confirmSoftOnOff)
            self.atualiza = html.I("restart_alt", 
                Class="w3-right material-icons w3-hover-pointer", 
                style="color:white")
            self.atualiza.bind("click", self.atualizaEstado)
            
            cabeca <= self.alteraEstado
            cabeca <= self.hardOff
            cabeca <= self.atualiza
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
        area1 = html.DIV(botaoLink("IPMI", f"http://{self.ipmi}"), Class=f"w3-col s4") #  w3-padding")
        area2 = html.DIV(f"{self.tipo}", Class=f"w3-col s4") #  w3-padding")
        area3 = html.DIV( "---", Class=f"w3-col s4") #  w3-padding")
        if self.temp:
            area3.innerHTML = f"{self.temp}°C"
        grid_container <= area1
        grid_container <= area2
        grid_container <= area3
        self <= grid_container
    def confirmaHardOFF(self, evt):	
        conf = html.SPAN("DESLIGAR - HARD OFF "+self.nome+ "?", Class="w3-red")	
        Confirma(conf, self.hardOFF)
    def atualizaEstado(self, evt):
        self.atualiza.classList.add("w3-hide")
        self.setPower("status")
    def hardOFF(self):
        alert("HARD OFF")
        self.setPower("off")
    def confirmSoftOnOff(self, evt):
        if self.status:
            Confirma("Confirma SOFT OFF?", self.softOff)
        else:
            Confirma("Confirma ON?", self.powerON)
    def softOff(self):
        # alert("SOFT")
        self.setPower("shutdown")
    def powerON(self):
        # alert("ON")
        self.setPower("on")

    def setPower(self, action):
        ajax.post("/hosts/power", 
            data=json.dumps({
                'password': self.pwipmi,
                'ipmiip':self.ipmi,
                'action':action}), 
            oncomplete=self.powerActionExecuted,
            headers={"Content-Type":"application/json"})
    def powerActionExecuted(self,res):
        resposta = res.json
        try:
            if resposta["powerstate"]=='off':
                self.status = False
            elif resposta["powerstate"]=='on':
                
                self.status = True
        except:
            alert(str(resposta))
        self.updateAparencia()
        
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
        self.autentica=""
        self.cabeca = Cabecalho(self.updateView)
        self <= self.cabeca
        self.corpo = html.DIV()
        self <= self.corpo


    def updateView(self):
        self.corpo.innerHTML = ""
        if self.cabeca.mode=="grid":
            self.corpo <= GridServidores(self.cabeca)
            self.cabeca.grafViewIcon.style = {'color':'white'}
            self.cabeca.gridViewIcon.style = {'color':'grey'}
        elif self.cabeca.mode=="temp":
            self.corpo.style={'height':"90vh", 'width':"100vw"}
            tempSeries = html.IFRAME(src="/temps", style={'height':"100%", 'width':"100%"})
            self.corpo <= tempSeries
            self.cabeca.gridViewIcon.style = {'color':'white'}
            self.cabeca.grafViewIcon.style = {'color':'grey'}


document <= Principal()

