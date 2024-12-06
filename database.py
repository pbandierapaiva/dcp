### Class DB

import mysql.connector as mariadb
from pydantic import BaseModel
from typing import Optional
from conexao import conexao

class DB:
    def __init__(self):
        self.con= mariadb.connect(**conexao)
        #self.con= mysqlconnector.connect(**conexao)
        self.cursor= self.con.cursor(dictionary=True)
    def commit(self):
        self.con.commit()

class NetDev(BaseModel):
	ip: str
	rede: str
	ether: Optional[str]
	maq: int

class HostInfo(BaseModel):
	hostid:Optional[int]
	nome: str
	comentario: Optional[str]
	estado: str
	tipo: Optional[str]
	hospedeiro: Optional[int]
	so: Optional[str]
	kernel: Optional[str]
	cpu: Optional[str]
	n: Optional[int]
	mem: Optional[int]

class Autentica(BaseModel):
	password: str

class ControlaPower(BaseModel):
	ipmiip: str
	password: str
	action: str