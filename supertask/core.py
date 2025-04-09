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
        pre_seed_jobs: str = None,
        debug: bool = False,
    ):
        # Bundle settings to be able to propagate them to the FastAPI subsystem.
        """
        Initializes a Supertask instance with a job store and settings.
        
        If the provided store is a string, it is converted to a JobStore instance using JobStore.from_address.
        Creates a Settings object with options to delete existing jobs and pre-seed jobs, and sets the debug mode.
          
        Args:
            store (JobStore or str): A job store instance or an address string to initialize one.
            pre_delete_jobs (bool): If True, deletes existing jobs during initialization.
            pre_seed_jobs (str, optional): Optional instructions for seeding jobs.
            debug (bool): Enables debug mode when set to True.
        """
        if isinstance(store, str):
            store = JobStore.from_address(store)
        self.settings = Settings(
            store=store,
            pre_delete_jobs=pre_delete_jobs,
            pre_seed_jobs=pre_seed_jobs,
        )
        self.debug = debug
        self.scheduler: BackgroundScheduler = None
        self.listen_http: t.Optional[str] = None

    def with_namespace(self, namespace: str) -> "Supertask":
        """
        Sets the namespace for the job store and returns the Supertask instance.
        
        This method updates the job store configuration with the provided namespace,
        allowing for namespacing of scheduled jobs to support logical grouping.
        
        Args:
            namespace: A string representing the namespace identifier for the job store.
        
        Returns:
            The Supertask instance with the updated namespace configuration.
        """
        self.settings.store.with_namespace(namespace)
        return self

    def configure(self):
        """
        Configures the scheduler based on the job store settings.
        
        Initializes the job store according to the URL scheme specified in the settings (using an
        in-memory store, a SQLAlchemy store for PostgreSQL, or a CrateDB-compatible store). If job
        deletion is enabled, existing jobs are removed before setting up the scheduler. A
        BackgroundScheduler is then created with defined executors, job defaults, and a fixed
        timezone (Europe/Vienna). Logs of the configuration parameters are generated.
        
        Returns:
            self: The instance with the configured scheduler.
        
        Raises:
            RuntimeError: If the job store address has an unknown scheme.
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
        """
        Set the HTTP server address for the instance.
        
        Args:
            listen_http: The address on which the HTTP server should listen.
        """
        self.listen_http = listen_http

    def start(self):
        """
        Starts the scheduler and HTTP service.
        
        Initializes the background scheduler and attempts to start the HTTP service, if configured. Returns the instance to support method chaining.
        """
        self.start_scheduler()
        self.start_http_service()
        return self

    def start_scheduler(self):
        """
        Starts the scheduler and logs next run times for all scheduled jobs.
        
        This method initiates the scheduler by calling its start method, logs a startup
        message, and then retrieves all scheduled jobs to log each job's identifier along
        with its next scheduled run time. It returns the current instance to enable method chaining.
        """
        logger.info("Starting scheduler")
        self.scheduler.start()

        # Get next run time for all jobs.
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            ic(job.id, job.next_run_time)
        return self

    def run_forever(self):
        """
        Continuously runs the application until interrupted.
        
        This method simulates ongoing activity by entering an infinite sleep loop while
        displaying a spinner and exit instructions. When a keyboard interrupt or system
        exit occurs, it gracefully shuts down the scheduler and returns the instance.
        
        Returns:
            The current instance.
        """
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
        """
        Starts the HTTP service if a listen address is configured.
        
        If the instance’s listen_http attribute is set, this method is intended to
        initialize and start an HTTP service to handle incoming requests. The actual
        HTTP service startup code is currently commented out, making this a placeholder.
        The method returns the instance itself.
        """
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
        """
        Executes the steps of a task payload.
        
        This method instantiates a Task using the provided keyword arguments and iterates over its defined steps.
        Steps with a falsy condition are logged as skipped. For steps marked as a "python-entrypoint", the method
        dynamically retrieves the corresponding function and calls it with the step's positional and keyword arguments,
        logging the function's result. If a step specifies an unsupported type, a RuntimeError is raised.
        
        Args:
            *args: Additional positional arguments (unused).
            **kwargs: Keyword arguments used to initialize the Task and define its steps.
        
        Raises:
            RuntimeError: If a task step specifies an unsupported type.
        """
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


taskrunner = TaskRunner()
