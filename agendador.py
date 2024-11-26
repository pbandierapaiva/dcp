## agendador.py agendaMonitoramento()
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import subprocess

# Function to be scheduled
def tarefaAgendada():
	print("Rodando monitoramento")
	executa = ["python", "sonda.py"]
	output = subprocess.run(executa, capture_output=True, text=True		)
	print(output.stdout)

def agendaMonitoramento():
    # Inicia scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()

    scheduler.add_job(
        tarefaAgendada,
        CronTrigger(minute="*/3"),  
        max_instances=3,
        misfire_grace_time=250,
        coalesce=True
    )
