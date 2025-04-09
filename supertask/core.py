import logging
import os
import time
import typing as t

import icecream
import pytz
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.util import ref_to_obj
from halo import Halo
from icecream import ic

from supertask.model import JobStore, Settings, Task
from supertask.store.cratedb import CrateDBSQLAlchemyJobStore

logger = logging.getLogger(__name__)

icecream.IceCreamDebugger.lineWrapWidth = 120


class Supertask:
    SQLALCHEMY_ECHO = False

    def __init__(
        self,
        store: t.Union[JobStore, str],
        pre_delete_jobs: bool = False,
        debug: bool = False,
    ):
        # Bundle settings to be able to propagate them to the FastAPI subsystem.
        if isinstance(store, str):
            store = JobStore.from_address(store)
        self.settings = Settings(
            store=store,
            pre_delete_jobs=pre_delete_jobs,
        )
        self.debug = debug
        self.scheduler: BackgroundScheduler = None
        self.listen_http: t.Optional[str] = None

    def with_namespace(self, namespace: str) -> "Supertask":
        self.settings.store.with_namespace(namespace)
        return self

    def configure(self):
        """
        https://apscheduler.readthedocs.io/en/3.x/userguide.html#configuring-the-scheduler
        """
        logger.info("Configuring scheduler")

        # Initialize a job store.
        address = self.settings.store.address
        schema = self.settings.store.schema
        table = self.settings.store.table
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

    def with_http_server(self, listen_http: str):
        self.listen_http = listen_http
        return self

    def start(self):
        self.start_scheduler()
        self.start_http_service()
        return self

    def start_scheduler(self):
        logger.info("Starting scheduler")
        self.scheduler.start()

        # Get next run time for all jobs.
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            ic(job.id, job.next_run_time)
        return self

    def run_forever(self):
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

    def start_http_service(self):
        if self.listen_http:
            # httpapi = HTTPAPI(settings=self.settings, listen_address=self.listen_http, debug=self.debug)  # noqa: ERA001, E501
            # httpapi.start()  # noqa: ERA001
            pass
        return self


class TaskRunner:
    """
    Execute task payloads.

    TODO: Capture and provide results.
    """

    def run(self, *args, **kwargs):
        task = Task(**kwargs)
        for step in task.steps:
            if not step.if_:
                logger.info(f"Skipping step {step.name}")
                continue
            if step.uses == "python-entrypoint":
                func = ref_to_obj(step.run)
                retval = func(*step.args, **step.kwargs)
                logger.info(f"Result: {retval}")
            else:
                raise RuntimeError(f"Unknown step type: {step.uses}")


# Global entrypoint for the scheduler.
taskrunner = TaskRunner()
