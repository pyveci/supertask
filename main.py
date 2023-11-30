from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from icecream import ic
import time
import uvicorn
import os
import pytz
import threading
from database import get_db, write_db
from halo import Halo
from scheduler import FileChangeHandler, my_job
from fastapi import FastAPI
from cronjob_routes import router as cronjob_router

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

app = FastAPI()
app.include_router(cronjob_router)
server_thread = threading.Thread(target=run_server)
server_thread.start()

# Create a timezone object for Vienna
timezone = pytz.timezone('Europe/Vienna')

job_defaults = {
    'coalesce': False,
    'max_instances': 1
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults, timezone=timezone)
scheduler.add_jobstore(MemoryJobStore(), 'default')

# Create an instance of FileChangeHandler with the scheduler
file_change_handler = FileChangeHandler(scheduler)

# Initial load of jobs from cronjobs.json
cronjobs = get_db()
for cronjob in cronjobs:
    if cronjob.enabled:
        ic(cronjob)
        minute, hour, day, month, day_of_week = cronjob.crontab.split()
        scheduler.add_job(my_job, 'cron', minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, id=str(cronjob.id), jobstore='default', args=[cronjob.job], max_instances=4)

scheduler.start()

# Watch cronjobs.json for changes in scheduled jobs
observer = Observer()
#observer.schedule(FileChangeHandler(), path=os.path.dirname(os.path.abspath('cronjobs.json')))
observer.schedule(file_change_handler, path=os.path.dirname(os.path.abspath('cronjobs.json')))
observer.start()

start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
ic('//======= START ======', start)

# Get next run time for all jobs
jobs = scheduler.get_jobs()
for job in jobs:
    ic(job.id, job.next_run_time)

print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
spinner = Halo(text='Waiting', spinner='dots')
spinner.start()
try:
    # This is here to simulate application activity (which keeps the main thread alive).
    while True:
        time.sleep(2)
except (KeyboardInterrupt, SystemExit):
    # Not strictly necessary if daemonic mode is enabled but should be done if possible
    scheduler.shutdown()
