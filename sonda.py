## sonda.py - módulo autônomo (standalone) para sondar servidores DCP
##
##

from database import DB, NetDev, HostInfo 
from conexao import conexao,botToken

from pyghmi.ipmi import command as IPMI

import requests
from tabulate import tabulate

from datetime import datetime,time
import pytz


def main():
    horasonda = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime('%Y-%m-%d %H:%M:%S')

    db = DB()
    db.cursor.execute("Select * from servidor where habilitado=1")	
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
            print(f"{reg['Nome']} Erro: {e}")           

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
    verificaStatus()
    print("Sonda concluída")

def verificaStatus():
    sql = """
        SELECT 
        DC,
        ROUND(AVG(temp), 2) AS avg_temp,
        SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END) AS stateOFF,
        SUM(CASE WHEN state = 1 THEN 1 ELSE 0 END) AS stateON,
        rodada
        FROM servidor_log
        WHERE rodada = (
        SELECT MAX(rodada) FROM servidor_log
        )
        GROUP BY DC;
        """
    db = DB()
    db.cursor.execute(sql)
    results = db.cursor.fetchall()
    
    for l in results:
        if ( l["DC"]=="DIS" and l["avg_temp"]>30 ) \
            or ( l["DC"]=="STI" and l["avg_temp"]>35 ):
            print("ATENÇÃO!\n",str(l))
            enviaTelegram(results)
        else:
            print("Status OK")
    
    # envia diário às 17h    
    now = datetime.now()
    current_time = now.time()  # Correctly access the time object
    start_time = time(17, 0, 0)  # 17:00:00
    end_time = time(17, 2, 59)   # 17:02:59 
    print(current_time)
    if start_time <= current_time <= end_time:
        enviaTelegram(results)
    
    sqlLimpa = """DELETE FROM servidor_log
        WHERE rodada < NOW() - INTERVAL 48 HOUR;"""
    db.cursor.execute(sqlLimpa)
    db.commit()

def enviaTelegram(jdata):
    BOT_TOKEN = botToken
    CHAT_ID = "5211765818"

    table_data = []
    for row in jdata:
        table_data.append([
            row['DC'],
            round(float(row['avg_temp']), 2),
            int(row['stateON']),
            int(row['stateOFF']),
            row['rodada'].strftime('%Y-%m-%d %H:%M'),
        ])

    # Format the table using tabulate
    headers = ["DC", "Avg Temp", " ON", "OFF", "Rodada"]
    table = tabulate(table_data, headers=headers, tablefmt="pretty")



    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"```\n{table}\n```",
        "parse_mode": "MarkdownV2",  # Use MarkdownV2 for monospaced text

    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("Mensagem Telegram enviada")
    else:
        print(f"Falha de envio: {response.status_code}, {response.text}")

if __name__ == '__main__':
    main()
    # x=verificaStatus()