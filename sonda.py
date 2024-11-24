## sonda.py - módulo autônomo (standalone) para sondar servidores DCP
##
from database import DB, NetDev, HostInfo 
from conexao import conexao

#import subprocess
from conexao import conexao, rootpw
from pyghmi.ipmi import command as IPMI

from datetime import datetime
import pytz


def main():
    horasonda = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime('%Y-%m-%d %H:%M:%S')

    db = DB()
    db.cursor.execute("Select * from servidor")	
    tudo = db.cursor.fetchall()

    for reg in tudo:
        insereCmd = """INSERT INTO servidor_log (id, ts, state, temp, rodada, DC) """

        ip = reg["IPMI_IP"]
        senha = reg["senhaIPMI"]

        try:
            ipmi_conn = IPMI.Command(bmc=ip, userid='admin', password=senha, keepalive=False)
            estado = ipmi_conn.get_power().get('powerstate')                                                        
                                                                                                            
        except Exception as e:    
            estado = None                                                                                 
            print(f"Erro: {e}")           

        if estado == 'on':                                                                                      
            try:                                                                                               
                temp = ipmi_conn.get_sensor_reading('System Temp').value                                       
            except:                                                                                            
                temp = None

        if estado== 'on':
                estadoSQL= 'True'  # Corresponds to SQL TRUE
        elif 'off':
                estadoSQL= 'False'  # Corresponds to SQL FALSE
        else:
                estadoSQL= 'NULL'  # Corresponds to SQL NULL
        
        id = reg["id"]
        DC = reg["DC"]
        if temp is None:
            insereCmd += f"""VALUES ({id}, CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo'),
                {estadoSQL}, NULL, '{horasonda}', '{DC}');"""
        else:
            insereCmd += f"""VALUES ({id}, CONVERT_TZ(NOW(), 'UTC', 'America/Sao_Paulo'),
                {estadoSQL}, {temp}, '{horasonda}', '{DC}');"""
        try:                                                                
            db.cursor.execute(insereCmd)
        except:
            print(insereCmd)
    db.commit()
    print("sonda concluída")
if __name__ == '__main__':
    main()