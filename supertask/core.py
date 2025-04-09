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
        Initializes a Supertask instance with a job store and task configuration options.
        
        If the provided store is a string, it is converted to a JobStore using its address.
        Job store settings along with options to pre-delete and pre-seed jobs are bundled into a
        Settings object. Debug mode is configured, and the scheduler and HTTP listener are initialized
        to None.
          
        Args:
            store: A JobStore instance or a string representing the job store address.
            pre_delete_jobs: If True, existing jobs will be removed before setup.
            pre_seed_jobs: Optional configuration for pre-seeding jobs.
            debug: Flag indicating whether debugging is enabled.
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
        Sets the job store namespace.
        
        Updates the job store configuration to use the specified namespace and returns the current
        Supertask instance, allowing for method chaining.
        
        Args:
            namespace: A string identifier for scoping job store entries.
        
        Returns:
            Supertask: The instance with the updated namespace.
        """
        self.settings.store.with_namespace(namespace)
        return self

    def configure(self):
        """
        Configures the scheduler based on job store settings.
        
        Initializes the job store using the address from settings, selecting a memory, PostgreSQL, or CrateDB
        backend depending on the address scheme. If pre-deletion is enabled, existing jobs are removed.
        The method then creates a BackgroundScheduler with default job settings, custom thread and process
        executors, and sets the timezone to Europe/Vienna.
        
        Returns:
            self: The instance with its scheduler configured.
        
        Raises:
            RuntimeError: If the job store address has an unsupported protocol.
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
        Sets the HTTP server listening address.
        
        Assigns the specified address to the instance for later use when starting the HTTP service.
        """
        self.listen_http = listen_http

    def start(self):
        """
        Starts the scheduler and HTTP service, then returns the instance.
        
        Initiates the scheduler to run background tasks and attempts to start the HTTP
        service if a listening address has been specified. Returns the current instance
        to enable chained operations.
        
        Returns:
            Supertask: The current instance.
        """
        self.start_scheduler()
        self.start_http_service()
        return self

    def start_scheduler(self):
        """
        Starts the scheduler and logs the next scheduled run times for all jobs.
        
        This method logs that the scheduler is starting, initiates the background scheduler,
        and then iterates over all registered jobs to log each job's identifier along with the
        next time it is scheduled to run. It returns the instance to allow method chaining.
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
        Run the application indefinitely until an exit signal is received.
        
        Prints exit instructions and starts a spinner indicator while the function enters an
        infinite loop to simulate ongoing activity. On receiving a KeyboardInterrupt or
        SystemExit, it gracefully shuts down the scheduler and returns the current instance.
        
        Returns:
            Self instance.
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
        
        If an HTTP listen address is set, this method is intended to initialize and start
        the corresponding HTTP API service using the current settings and debug mode.
        Currently, the service initialization code is commented out, making this a
        placeholder implementation.
        
        Returns:
            Self, to enable method chaining.
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
        Executes task steps sequentially.
        
        Instantiates a Task object using the provided keyword arguments and processes
        each of its steps in order. For any step where the condition is not met,
        logs that the step is skipped. For steps specifying a Python entry point,
        resolves and executes the corresponding function with the step’s arguments,
        logging its result. Raises a RuntimeError if an unrecognized step type is
        encountered.
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
