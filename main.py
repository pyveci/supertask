from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from icecream import ic
import time
import random
import os
import pytz
from database import get_db, write_db
from halo import Halo


# Create a timezone object for Vienna
timezone = pytz.timezone('Europe/Vienna')
scheduler = BackgroundScheduler(timezone=timezone)

#ic.configureOutput(prefix=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
#ic.configureOutput(includeContext=True)

class FileChangeHandler(FileSystemEventHandler):
  def on_modified(self, event):
      if not event.is_directory and event.src_path.endswith('cronjobs.json'):
          # Load jobs from cronjobs.json
          ic("FILE CHANGED")
          cronjobs = get_db()
          cronjob_ids = [str(cronjob.id) for cronjob in cronjobs]
          ic(cronjob_ids)

          # Get all existing jobs
          existing_jobs = scheduler.get_jobs()
          ic(existing_jobs)

          # Remove jobs that are not in cronjobs.json
          for job in existing_jobs:
              #ic("check-removale", job.id)
              if job.id not in cronjob_ids:
                  ic("REMOVE: ", job.id)
                  scheduler.remove_job(job.id)

          # Add jobs that are not in cronjobs.json
          for cronjob in cronjobs:
              #ic("check-add", cronjob.id)
              existing_job_ids = [job.id for job in existing_jobs]
              #ic(existing_job_ids)
              if cronjob.enabled and str(cronjob.id) not in existing_job_ids:
                  #ic("ADD: ", cronjob.id)
                  minute, hour, day, month, day_of_week = cronjob.crontab.split()
                  job = scheduler.add_job(my_job, 'cron', minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, id=str(cronjob.id), jobstore='default', args=[cronjob.job], max_instances=4)
                  ic("ADDED: ", cronjob.job, job.next_run_time)

          # Reschedule existing jobs
          for cronjob in cronjobs:
              if cronjob.enabled:
                  #ic(cronjob.id)
                  minute, hour, day, month, day_of_week = cronjob.crontab.split()
                  job = scheduler.reschedule_job(str(cronjob.id), trigger='cron', minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week)
                  ic("RESCHED: ", cronjob.job, job.next_run_time)

observer = Observer()
observer.schedule(FileChangeHandler(), path=os.path.dirname(os.path.abspath('cronjobs.json')))
observer.start()


def my_job(job="select 1"):
    random_number = random.randint(5, 10)
    start=time.strftime("%H:%M:%S", time.localtime())
    ic(start, job)
    time.sleep(random_number)
    end=time.strftime("%H:%M:%S", time.localtime())
    ic("DONE", end, job)

scheduler = BackgroundScheduler()
scheduler.add_jobstore(MemoryJobStore(), 'default')

cronjobs = get_db()
for cronjob in cronjobs:
    if cronjob.enabled:
        ic(cronjob)
        minute, hour, day, month, day_of_week = cronjob.crontab.split()
        #scheduler.add_job(my_job, 'cron', minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, jobstore='default', id=cronjob.id, args=[cronjob.job], max_instances=4)
        scheduler.add_job(my_job, 'cron', minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, id=str(cronjob.id), jobstore='default', args=[cronjob.job], max_instances=4)

# Pass the function `my_job`, not `my_job("job1")`
#scheduler.add_job(my_job, 'cron', minute='*', jobstore='default', args=["job1"], max_instances=4)
#scheduler.add_job(my_job, 'cron', minute='*', jobstore='default', args=["job2"], max_instances=4)

scheduler.start()
start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
ic(start)

jobs = scheduler.get_jobs()
for job in jobs:
    ic(job.id, job.next_run_time)

spinner = Halo(text='Waiting', spinner='dots')
spinner.start()

# Block the main thread
while True:
    spinner.stop()
    #print (f'Current time: {time.strftime("%H:%M:%S", time.localtime())}')
    spinner.start()
    time.sleep(5)
