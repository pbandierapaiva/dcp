from browser import document
from browser import html, ajax, alert, confirm, prompt

from browser.widgets.dialog import InfoDialog, Dialog

import json


class GridServidores(html.DIV):
    def __init__(self):
        html.DIV.__init__(self,Class="grid-container")
        self.loadServerData()
        self.servidores = []
    def loadServerData(self):
        ajax.get("/hosts", oncomplete=self.dataLoaded)
    def dataLoaded(self, res):
        hostlist = res.json
        # alert(len(hostlist))
        for item in hostlist:
            serv =  CaixaServidor(item)
            self.servidores.append(serv)
            self <= serv
    def update(self):
        for s in self.servidores:
            s.update()

class CaixaServidor(html.DIV):
    def __init__(self, data):
        html.DIV.__init__(self,Class="w3-card-4 server-box")
        self.id = data["id"]
        self.nome = data["Nome"]
        self.ipmi = data["IPMI_IP"]
        self.pwipmi = data["senhaIPMI"]
        self.hostip = data["HostIP"]
        self.usrip = data["IP_USER"]
        self.dc = data["DC"]
        self.tipo = data["H_S_X"]
        self.desc = data["Descricao"]
        self.temp = data["temp"]
        self.status = data["state"]
        cabeca = html.HEADER( self.id+"-"+self.nome, Class="w3-container ")
        self.caixa = html.DIV(Class="w3-container ")
        self <= cabeca
        self<= self.caixa

        # alert(self.id+"-"+self.nome+"-"+str(self.temp))
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
        self.caixa.innerHTML = str(self.temp)
        # self.update()






    def update(self):
        ajax.get("/hosts/%s/status"%self.id, oncomplete=self.dataLoaded)
    def dataLoaded(self,res):
        try:
            self.status = res.json["power"]
        except:
            self.status = None
        try:
            self.temp = float( res.json["temp"] )
        except:
            self.temp = None

        corcaixa=""
        if self.status:
            if self.temp>30:
                corcaixa="w3-light-red"
            else:
                corcaixa="w3-light-green"
        else:
            if self.status is None:
                corcaixa="w3-white"
            else: # OFF
                corcaixa="w3-light-grey"
        self.classList.add(corcaixa)
        self.caixa.innerHTML = str(self.temp)

cabecalho = html.DIV("DCP-DIS-EPM-Unifesp", id="cabecalho", Class="w3-bar w3-card-2 w3-blue notranslate")

document <= cabecalho

document <= GridServidores()
 