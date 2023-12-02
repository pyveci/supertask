import logging

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
from util import setup_logging

logger = logging.getLogger(__name__)


class Supertask:

    def __init__(self):
        self.scheduler: BackgroundScheduler = None
        self.configure()

    def configure(self):
        logger.info("Configuring scheduler")
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }

        # Create a timezone object for Vienna
        timezone = pytz.timezone('Europe/Vienna')
        self.scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults, timezone=timezone)
        self.scheduler.add_jobstore(MemoryJobStore(), 'default')
        logger.info(f"Configured scheduler: "
                    f"executors={self.scheduler._executors}, "
                    f"jobstores={self.scheduler._jobstores}, "
                    f"timezone={self.scheduler.timezone}"
                    )
        return self

    def start(self):
        self.start_scheduler()
        self.start_filesystem_observer()
        self.start_http_service()
        return self

    def start_scheduler(self):
        logger.info("Starting scheduler")
        self.scheduler.start()
        start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        ic('//======= START ======', start)

        # Get next run time for all jobs
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            ic(job.id, job.next_run_time)
        return self

    def wait(self):
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        spinner = Halo(text='Waiting', spinner='dots')
        spinner.start()
        try:
            # This is here to simulate application activity (which keeps the main thread alive).
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            self.scheduler.shutdown()
        return self

    def seed_jobs(self):
        logger.info("Seeding jobs")
        # Initial load of jobs from cronjobs.json
        cronjobs = get_db()
        for cronjob in cronjobs:
            if cronjob.enabled:
                ic(cronjob)
                minute, hour, day, month, day_of_week = cronjob.crontab.split()
                self.scheduler.add_job(my_job, 'cron', minute=minute, hour=hour, day=day, month=month,
                                       day_of_week=day_of_week, id=str(cronjob.id), jobstore='default', args=[cronjob.job],
                                       max_instances=4)
        return self

    def start_filesystem_observer(self):
        logger.info("Starting filesystem observer")
        # Create an instance of FileChangeHandler with the scheduler
        file_change_handler = FileChangeHandler(self.scheduler)

        # Watch cronjobs.json for changes in scheduled jobs
        observer = Observer()
        # observer.schedule(FileChangeHandler(), path=os.path.dirname(os.path.abspath('cronjobs.json')))
        observer.schedule(file_change_handler, path=os.path.dirname(os.path.abspath('cronjobs.json')))
        observer.start()
        return self

    def start_http_service(self):
        logger.info("Starting HTTP service")
        app = FastAPI()
        app.include_router(cronjob_router)

        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=8000)

        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        return self


def main():
    setup_logging()
    st = Supertask()
    st.seed_jobs()
    st.start()
    st.wait()


if __name__ == "__main__":
    main()
