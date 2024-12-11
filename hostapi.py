## hostapi.py - servidor FASTAPI para monitoramento do DC

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

# Para gráficos de temperatura:
import matplotlib
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import pandas as pd
import matplotlib.dates as mdates
matplotlib.use("Agg")

# Para IPMI
from pyghmi.ipmi import command as IPMI
from pyghmi.exceptions import IpmiException  # Import IpmiException

from database import DB, NetDev, HostInfo, Autentica, ControlaPower
from agendador import agendaMonitoramento
from conexao import conexao, botToken

# from conexao import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES,
from conexao import ADMIN_PASSWORD

import paramiko
from paramiko.client import SSHClient, AutoAddPolicy

app = FastAPI()
agendaMonitoramento()

app.mount("/web", StaticFiles(directory="web"), name="web")

@app.get("/")
async def root():
    return RedirectResponse("/web/host.html")

####################################

####################################

# BASE_URL = f"https://api.telegram.org/bot{botToken}"

# # Entrada para Telegram webhook
# @app.post("/webhook")
# async def handle_webhook(request: Request):
#     data = await request.json()  # Get the JSON payload from Telegram
#     print("Recebeu update:", json.dumps(data, indent=2))

#     # Process the update
#     if "message" in data:
#         chat_id = data["message"]["chat"]["id"]
#         text = data["message"].get("text", "")

#         # Respond to the user
#         reply_text = f"You said: {text}"
#         send_message(chat_id, reply_text)

#     return {"status": "ok"}

# def send_message(chat_id: int, text: str):
#     """
#     Envia mensagem via Telegram bot.
#     """
#     url = f"{BASE_URL}/sendMessage"
#     payload = {
#         "chat_id": chat_id,
#         "text": text,
#     }
#     response = requests.post(url, json=payload)
#     if response.status_code != 200:
#         print(f"Falha ao enviar mensagem: {response.text}")

# # Configura o webhook do Telegram
# @app.on_event("startup")
# def set_webhook():
#     webhook_url = "https://your-server-url/webhook" 
#     url = f"{BASE_URL}/setWebhook"
#     payload = {"url": webhook_url}
#     response = requests.post(url, json=payload)
#     if response.status_code == 200:
#         print("Webhook set successfully!")
#     else:
#         print(f"Failed to set webhook: {response.text}")

# Sample data: timestamps and average temperatures
timestamps = [
    "2024-12-01 12:00", "2024-12-02 12:00", "2024-12-03 12:00",
    "2024-12-04 12:00", "2024-12-05 12:00"
]
temperatures = [15.5, 17.3, 14.8, 16.1, 15.9]

# Convert timestamps to datetime objects
timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M") for ts in timestamps]

@app.get("/temps", response_class=HTMLResponse)
def home():
	sql = """
	SELECT 
	DC,
	ROUND(AVG(temp), 2) AS avg_temp,
	SUM(CASE WHEN state = 1 THEN 1 ELSE 0 END) AS stateON,
	SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END) AS stateOFF,
	rodada
	FROM servidor_log
	GROUP BY rodada, DC;
	"""
	db = DB()
	db.cursor.execute(sql)
	rows = db.cursor.fetchall()
	columns = [desc[0] for desc in db.cursor.description]
	data = pd.DataFrame(rows, columns=columns)

	# Convert 'rodada' column to datetime
	data["rodada"] = pd.to_datetime(data["rodada"])
	data["date"] = data["rodada"].dt.date  # Extract the date
	data["time"] = data["rodada"].dt.time  # Extract the time

	# Combine 'date' and 'time' into full datetime objects
	data["datetime"] = data.apply(lambda row: datetime.combine(row["date"], row["time"]), axis=1)

	# Group data by 'date' and plot separate lines for each date
	plt.figure(figsize=(10, 5))
	colors = {'DIS': 'green', 'STI': 'blue'}  # Define colors for each DC category
	
	added_labels =set()

	for (dc, date), group in data.groupby(["DC", "date"]):
		label = dc if dc not in added_labels else None  # Add label only for first occurrence
		plt.plot(
			group["datetime"],  # Use full datetime objects for x-axis
			group["avg_temp"],
			linestyle='-',  # Line without markers
			label=label,
			color=colors[dc]
		)
		added_labels.add(dc)


	# Format the x-axis to show time in HH:MM format
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

	# Add details to the chart
	plt.title("Temperatura média dos servidores (intervalos de 3min)")
	plt.xlabel("Horário")
	plt.ylabel("Temp. média (°C)")
	plt.grid(True)
	plt.legend(title="Datacenter")

	# Save the plot to a BytesIO object
	img = io.BytesIO()
	plt.savefig(img, format="png")
	img.seek(0)
	plt.close()

	# Encode the plot to Base64 to embed in HTML
	plot_url = base64.b64encode(img.getvalue()).decode("utf8")

	# Render the HTML with the plot
	html = f"""
	<!DOCTYPE html>
	<html lang="en">
	<head>
		<title>Temperaturas</title>
	</head>
	<body>
		<!-- <h1>Temperatura nos Datacenters 48h</h1>
		-->
		<img src="data:image/png;base64,{plot_url}" alt="Grafico de temperaturas">
	</body>
	</html>
	"""
	return HTMLResponse(content=html)

	

@app.get("/DC")
async def DCstatus():
	## SQL para pegar as últimas sondagens de todos os servidores ligados
	## e calcular a temperatura média dos ambientes STI e DCP
	sql = """
	SELECT 
	DC,
	ROUND(AVG(temp), 2) AS avg_temp,
	SUM(CASE WHEN state = 1 THEN 1 ELSE 0 END) AS stateON,
	SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END) AS stateOFF,
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
	return JSONResponse(content=jsonable_encoder(results))	

@app.post("/hosts")
async def host(autentica : Autentica):
	sql=f"""
		WITH ranked_records AS (
			SELECT 
				servidor.id,
				servidor.Nome,
				{"servidor.senhaIPMI," if autentica.password==ADMIN_PASSWORD else ""}
				servidor.IPMI_IP,	
				servidor.HostIP,	
				servidor.IP_USER,	
				servidor.DC,	
				servidor.H_S_X,	
				servidor.Descricao,		
				servidor.habilitado,		
				servidor_log.ts,
				servidor_log.state,
				servidor_log.temp,
				servidor_log.rodada,
				servidor_log.DC AS DC_log,
				ROW_NUMBER() OVER (PARTITION BY servidor.id ORDER BY servidor_log.ts DESC) AS rnk
			FROM servidor
			INNER JOIN servidor_log ON servidor.id = servidor_log.id
			WHERE servidor.habilitado = 1 
			AND servidor_log.rodada = (SELECT MAX(rodada) FROM servidor_log)
		)
		SELECT * 
		FROM ranked_records
		WHERE rnk = 1;

	"""
	db = DB()
	db.cursor.execute(sql)
	tudo = db.cursor.fetchall()
	res = {} 
	if autentica.password==ADMIN_PASSWORD:
		res["Autenticado"]= True
	else:
		res["Autenticado"]= False
	res["result"] = tudo
	return JSONResponse(content=jsonable_encoder(res))

@app.post("/hosts/{hostid}")
async def host(hostid, autentica : Autentica):
	res = {}
	res["id"] = hostid
	if autentica.password==ADMIN_PASSWORD:
		res["Autenticado"]= True
	else:
		res["Autenticado"]= False	
	sql=f"""
			SELECT 
				servidor.id,
				servidor.Nome,
				servidor.HostIP,	
				servidor.IP_USER,	
				servidor.DC,	
				servidor.H_S_X,	
				servidor.Descricao,		
				servidor.habilitado		
			FROM servidor
			WHERE servidor.id = {res["id"]}
		"""	
	db = DB()
	db.cursor.execute(sql)
	# res["servidor"] = db.cursor.fetchone()
	dados = db.cursor.fetchone()
	# return JSONResponse(content=jsonable_encoder(dados))

	client = SSHClient()	
	client.set_missing_host_key_policy(AutoAddPolicy())
	chavePrivada = paramiko.ECDSAKey.from_private_key_file('dcp_ecdsa.key')
	try:
		client.connect(dados['HostIP'],username='root',pkey=chavePrivada)
		stdin, stdout, stderr = client.exec_command("virsh list --all")
		saida = stdout.read().decode().split('\n')
		erro = stderr.read().decode()
	except Exception as ex:
		template = "ERRO: {0} Parâmetros:\n{1!r}"
		m = template.format(type(ex).__name__, ex.args)
		return JSONResponse(content=jsonable_encoder({'STATUS':'ERROR', 'MSG':m}))

	if len(saida)>0: del saida[0]
	if len(saida)>0: del saida[0]
	if saida[-1]=='': del saida[-1]
	if saida[-1]=='': del saida[-1]

	resultado = {}
	for line in saida:
		parts = line.split()
		servidor = parts[1]  # The second column
		status = parts[-1]    # The last column
		resultado[servidor] = status == "running"


	# del saida[0]
	# del saida[-1]
	
	
	return JSONResponse(content=jsonable_encoder(resultado))


@app.post("/hosts/power")
async def host( controla : ControlaPower):
	print(controla.action, controla.ipmiip)
	try:	
		ipmi_conn = IPMI.Command(bmc=controla.ipmiip, userid='admin', password=controla.password) #, keepalive=False)
	except IPMI.IpmiException as e:
		return JSONResponse(content=jsonable_encoder({"ERROR":e, "type":"Connection"}))
	try:
		if controla.action=='status':
			retorno = ipmi_conn.get_power()
			print(retorno)
		else:
			retorno = ipmi_conn.set_power(controla.action, wait=True)
	except IpmiException as e:
		return JSONResponse(content=jsonable_encoder({"ERROR":e, "type":"Action", "command":controla.action}))
	except Exception as e:
		return JSONResponse(content=jsonable_encoder({"ERROR":e}))
	return JSONResponse(content=jsonable_encoder(retorno))