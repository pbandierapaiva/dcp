from browser import document
from browser import html, ajax, alert, confirm, prompt

from browser.widgets.dialog import InfoDialog, Dialog

from rack import *
from hostinfo import *
from utils import *

import json

cabecalho = html.DIV("DCP-DIS-EPM-Unifesp", id="cabecalho", Class="w3-bar w3-card-2 w3-blue notranslate")
busca = html.A(Class="w3-bar-item w3-button w3-hover-none w3-left w3-padding-4  w3-blue")
busca <= html.I(Class="fa fa-search")
busca.bind("click", buscaNo)
cabecalho<=busca

document <= cabecalho
document <= Rack()
document <= InfoArea()
