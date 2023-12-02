import logging
import icecream
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from icecream import ic
import time
import uvicorn
import os
import pytz
import threading
from halo import Halo

from job_seeder import JobSeeder
from jobstore_sqlalchemy import CrateDBSQLAlchemyJobStore
from fastapi import FastAPI
from cronjob_routes import router as cronjob_router
from util import setup_logging

logger = logging.getLogger(__name__)

icecream.IceCreamDebugger.lineWrapWidth = 120


class Supertask:

    def __init__(self, job_store_address: str, pre_delete_jobs: bool = False):
        self.job_store_address = job_store_address
        self.pre_delete_jobs = pre_delete_jobs
        self.scheduler: BackgroundScheduler = None
        self.configure()

    def configure(self):
        """
        https://apscheduler.readthedocs.io/en/3.x/userguide.html#configuring-the-scheduler
        """
        logger.info("Configuring scheduler")

        # Initialize a job store.
        if self.job_store_address.startswith("memory://"):
            job_store = MemoryJobStore()
        elif self.job_store_address.startswith("postgresql://"):
            job_store = SQLAlchemyJobStore(url=self.job_store_address, engine_options={"echo": True})
        elif self.job_store_address.startswith("crate://"):
            job_store = CrateDBSQLAlchemyJobStore(url=self.job_store_address, engine_options={"echo": True})
        else:
            raise RuntimeError(f"Initializing job store failed. Unknown address: {self.job_store_address}")

        if self.pre_delete_jobs:
            try:
                job_store.remove_all_jobs()
            except:
                pass

        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }
        job_stores = {
            'default': job_store,
        }

        # Create a timezone object for Vienna
        timezone = pytz.timezone('Europe/Vienna')
        self.scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults, jobstores=job_stores, timezone=timezone)
        logger.info(f"Configured scheduler: "
                    f"executors={self.scheduler._executors}, "
                    f"jobstores={self.scheduler._jobstores}, "
                    f"timezone={self.scheduler.timezone}"
                    )
        return self

    def start(self, listen_http: str = None):
        self.start_scheduler()
        if listen_http:
            self.start_http_service(listen_http)
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

    def start_http_service(self, listen_http: str):

        host, port_str = listen_http.split(":")
        port = int(port_str)

        logger.info(f"Starting HTTP service on: {host}:{port}")
        app = FastAPI()
        app.include_router(cronjob_router)

        def run_server():
            uvicorn.run(app, host=host, port=port)

        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        return self
