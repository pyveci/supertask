from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileSystemEventHandler
from icecream import ic
from database import get_db, write_db
from datetime import datetime

import random
import time

def my_job(job="select 1"):
    random_number = random.randint(5, 10) # mock diffenrent job run times
    start_time_str = time.strftime("%H:%M:%S", time.localtime())
    time.sleep(random_number)
    ic("DONE", start_time_str , random_number , job)

class FileChangeHandler(FileSystemEventHandler):  # pragma: nocover
  def __init__(self, scheduler):
      self.scheduler = scheduler
      self.last_modified = time.time()

  def on_modified(self, event):
      if time.time() - self.last_modified < 1:
          return

      self.last_modified = time.time()

      if not event.is_directory and event.src_path.endswith('cronjobs.json'):
          # Load jobs from cronjobs.json
          ic("FILE CHANGED")
          cronjobs = get_db()
          cronjob_ids = [str(cronjob.id) for cronjob in cronjobs]
          ic(cronjob_ids)

          # Get all existing jobs
          existing_jobs = self.scheduler.get_jobs()
          ic(existing_jobs)

          # Remove jobs that are not in cronjobs.json
          for job in existing_jobs:
              #ic("check-removale", job.id)
              if job.id not in cronjob_ids:
                  ic("REMOVE: ", job.id)
                  self.scheduler.remove_job(job.id)

          # Add jobs that are not in cronjobs.json
          for cronjob in cronjobs:
              #ic("check-add", cronjob.id)
              existing_job_ids = [job.id for job in existing_jobs]
              #ic(existing_job_ids)
              if cronjob.enabled and str(cronjob.id) not in existing_job_ids:
                  #ic("ADD: ", cronjob.id)
                  minute, hour, day, month, day_of_week = cronjob.crontab.split()
                  job = self.scheduler.add_job(my_job, 'cron', minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week, id=str(cronjob.id), jobstore='default', args=[cronjob.job])
                  next_run_time = job.trigger.get_next_fire_time(None, datetime.now())
                  ic("ADDED: ", cronjob.job, next_run_time)

          # Reschedule existing jobs
          for cronjob in cronjobs:
              if cronjob.enabled:
                  #ic(cronjob.id)
                  minute, hour, day, month, day_of_week = cronjob.crontab.split()
                  job = self.scheduler.reschedule_job(str(cronjob.id), trigger='cron', minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week)
                  ic("RESCHED: ", cronjob.job, job.next_run_time)
