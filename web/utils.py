from browser import document
from browser import html, ajax, alert, confirm, prompt

from browser.widgets.dialog import InfoDialog, Dialog

from hostinfo import *

class Cabecalho(html.DIV):
	def __init__(self):
		html.DIV.__init__(self, "DCP-DIS-EPM-Unifesp", id="cabecalho",
			Class="w3-bar w3-card-2 w3-grey notranslate")
		busca = html.A(Class="w3-bar-item w3-button w3-hover-none w3-left w3-padding-4  w3-right")
		busca <= html.I(Class="fa fa-search")
		busca.bind("click", buscaNo)


class Alerta(html.DIV):
	def __init__(self, msg, tit="Atenção", senha=False):
		html.DIV.__init__(self, Class="w3-modal")
		self.modal = html.DIV(Class="w3-modal-content")
		self.modal <= html.DIV(Class="w3-container w3-blue-grey") <= html.P(tit)
		self.cont = html.DIV(Class="w3-container")
		fecha = html.SPAN("&times", Class="w3-button w3-display-topright")
		fecha.bind("click", self.dismiss)
		self.cont <= fecha
		self.mensagem = html.P(msg)
		self.cont <= self.mensagem
		self <= self.modal <= self.cont
		document["dialog"].innerHTML=""
		document["dialog"] <= self
		self.style.display='block'
	def setmsg	(self, msg):
		self.mensagem.innerHTML = msg
	def dismiss(self,ev=0):
		self.style.display='none'

class PegaTexto(Alerta):
	def __init__(self, msg, callback, tit="Entre com texto", senha=False):
		Alerta.__init__(self, msg, tit)
		self.callback = callback
		self.inputCpo = html.INPUT(autofocus=True, type="password")
		self.inputCpo.className = "w3-input w3-border"
		botaoConfirma = html.DIV("OK", Class="w3-button w3-block")
		botaoConfirma.bind("click", self.confirma)
		self.modal <= self.inputCpo
		self.modal <= botaoConfirma
	def confirma(self, ev):
		self.style.display='none'
		self.callback(self.inputCpo.value)

class Confirma(Alerta):
	def __init__(self, msg, callback, titulo='Confirme'):
		Alerta.__init__(self, msg, titulo)
		self.callback = callback
		botaoConfirma = html.DIV("Sim", Class="w3-button")
		botaoConfirma.bind("click", self.confirma)
		botaoCancela = html.DIV("Não", Class="w3-button")
		botaoCancela.bind("click", self.dismiss)
		self.cont <= botaoConfirma
		self.cont <= botaoCancela

	def confirma(self, ev):
		self.style.display='none'
		self.callback()

class EntraTexto(html.DIV):
	def __init__(self, labelStr, valor="", width=""):
		html.DIV.__init__(self)
		if width !="":
			self.style = {"width":width}
		self.inputLbl = html.LABEL(labelStr)
		self.inputCpo = html.INPUT()
		self.inputCpo.value = valor
		self.inputCpo.className = "w3-input w3-border"
		self.inputCpo.disabled = True
		self.alterado = False
		self.inputCpo.bind("change", self.onChange)
		self <= self.inputLbl
		self <= self.inputCpo
	def enable(self):
		self.inputCpo.disabled = False
	def onChange(self,ev):
		self.alterado = True
	def valor(self):
		return self.inputCpo.value
	def setavalor(self, val):
		self.inputCpo.value= val
		self.alterado = True

class RadioEstado(html.DIV):
		def __init__(self, estado):
			html.DIV.__init__(self)
			self.estado = estado
			self.alterado = False
			self.estadoON = html.INPUT(name='restado', value="1",type = "radio")
			self.estadoON.disabled = True
			if( self.estado=="1" ):  self.estadoON.checked = True
			# self <= self.estadoON
			labON = html.LABEL("ON", Class = "radio-inline")
			labON <= self.estadoON
			self <= labON 
			self.estadoOFF = html.INPUT(name='restado', value="0", type = "radio")
			if( self.estado=="0" ): self.estadoOFF.checked = True
			self.estadoOFF.disabled = True
			# self <=  self.estadoOFF
			labOFF = html.LABEL(" OFF", Class = "radio-inline") 
			labOFF <=  self.estadoOFF
			self <= labOFF
			self.estadoOFF.bind("change",self.onChange)
			self.estadoON.bind("change",self.onChange)
		def enable(self):
			self.estadoOFF.disabled = False
			self.estadoON.disabled = False
		def onChange(self, ev):
			self.alterado = True
		def valor(self):
			if self.estadoOFF.checked: return "0"
			if self.estadoON.checked: return "1"
			return None


