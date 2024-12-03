## hostapi.py - servidor FASTAPI para monitoramento do DC

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from pyghmi.ipmi import command as IPMI

from database import DB, NetDev, HostInfo 
from agendador import agendaMonitoramento
from conexao import conexao, botToken

# from conexao import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES,ADMIN_PASSWORD
from paramiko.client import SSHClient, AutoAddPolicy

app = FastAPI()
agendaMonitoramento()

app.mount("/web", StaticFiles(directory="web"), name="web")

@app.get("/")
async def root():
    return RedirectResponse("/web/host.html")

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

@app.get("/hosts")
async def host():
	# sql = '''
	# SELECT 
	# 	servidor.*,
	# 	servidor_log.ts,
	# 	servidor_log.state,
	# 	servidor_log.temp,
	# 	servidor_log.rodada,
	# 	servidor_log.DC AS DC_log
	# FROM servidor
	# INNER JOIN servidor_log ON servidor.id = servidor_log.id
	# WHERE servidor_log.rodada = (
	# 	SELECT MAX(rodada) FROM servidor_log
	# );
	# '''
	sql="""
		WITH ranked_records AS (
			SELECT 
				servidor.*,
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
	return JSONResponse(content=jsonable_encoder(tudo))

