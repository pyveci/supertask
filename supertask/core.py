import logging
import os
import threading
import time
import typing as t

import icecream
import pytz
import uvicorn
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from halo import Halo
from icecream import ic

from supertask.http.routes import router as cronjob_router
from supertask.model import JobStoreLocation
from supertask.settings import Settings
from supertask.store.sqlalchemy import CrateDBSQLAlchemyJobStore

logger = logging.getLogger(__name__)

icecream.IceCreamDebugger.lineWrapWidth = 120


class Supertask:
    SQLALCHEMY_ECHO = False

    def __init__(
        self,
        store: t.Union[JobStoreLocation, str],
        pre_delete_jobs: bool = False,
        pre_seed_jobs: str = None,
        debug: bool = False,
    ):
        # Bundle settings to be able to propagate them to the FastAPI subsystem.
        if isinstance(store, str):
            store = JobStoreLocation(address=store)
        self.settings = Settings(
            store_location=store,
            pre_delete_jobs=pre_delete_jobs,
            pre_seed_jobs=pre_seed_jobs,
        )
        self.debug = debug
        self.scheduler: BackgroundScheduler = None
        self.configure()

    def configure(self):
        """
        https://apscheduler.readthedocs.io/en/3.x/userguide.html#configuring-the-scheduler
        """
        logger.info("Configuring scheduler")

        # Initialize a job store.
        address = self.settings.store_location.address
        schema = self.settings.store_location.schema
        table = self.settings.store_location.table
        if address.startswith("memory://"):
            job_store = MemoryJobStore()
        elif address.startswith("postgresql://"):
            # TODO: Need to run `CREATE SCHEMA ...` before using it?
            job_store = SQLAlchemyJobStore(url=address, tablename=table, engine_options={"echo": self.SQLALCHEMY_ECHO})
        elif address.startswith("crate://"):
            job_store = CrateDBSQLAlchemyJobStore(
                url=address, tableschema=schema, tablename=table, engine_options={"echo": self.SQLALCHEMY_ECHO}
            )
        else:
            raise RuntimeError(f"Initializing job store failed. Unknown address: {address}")

        if self.settings.pre_delete_jobs:
            try:
                job_store.remove_all_jobs()
            except Exception:  # noqa: S110
                pass

        job_defaults = {"coalesce": False, "max_instances": 1}
        executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}
        job_stores = {
            "default": job_store,
        }

        # Create a timezone object for Vienna
        timezone = pytz.timezone("Europe/Vienna")
        self.scheduler = BackgroundScheduler(
            executors=executors, job_defaults=job_defaults, jobstores=job_stores, timezone=timezone
        )
        logger.info(
            f"Configured scheduler: "
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
        ic("//======= START ======", start)

        # Get next run time for all jobs
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            ic(job.id, job.next_run_time)
        return self

    def wait(self):
        print("Press Ctrl+{0} to exit".format("Break" if os.name == "nt" else "C"))  # noqa: T201
        spinner = Halo(text="Waiting", spinner="dots")
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
        app = FastAPI(debug=self.debug)

        # Inject settings as dependency to FastAPI. Thanks, @Mause.
        # https://github.com/tiangolo/fastapi/issues/2372#issuecomment-732492116
        app.dependency_overrides[Settings] = lambda: self.settings

        app.include_router(cronjob_router)

        def run_server():
            uvicorn.run(app, host=host, port=port)

        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        return self
