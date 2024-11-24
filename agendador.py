## agendador.py agendaMonitoramento()
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import subprocess

# Function to be scheduled
def my_scheduled_task():
	print("Scheduled task is running!")
	executa = ["python", "sonda.py"]
	output = subprocess.run(executa, capture_output=True, text=True		)
	print(output.stdout)

def agendaMonitoramento():
    # Inicia scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()

    scheduler.add_job(
        my_scheduled_task,
        CronTrigger(minute="*/3"),  # Equivalent to a cronjob running every minute
        max_instances=3,
        misfire_grace_time=250,
        coalesce=True
    )
