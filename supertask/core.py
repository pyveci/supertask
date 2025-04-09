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
        Initialize a Supertask instance with job store configuration settings.
        
        If the store is provided as a string, it is converted to a JobStore using the from_address
        factory method. This constructor bundles settings for job deletion, pre-seeding, and debugging
        for use by the scheduler and HTTP subsystems.
        
        Args:
            store: A JobStore instance or an address string used to create one.
            pre_delete_jobs: If True, removes existing jobs during configuration.
            pre_seed_jobs: Optional identifier for pre-seeding jobs.
            debug: Enables debug mode if set to True.
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
            Configures the job store with the specified namespace.
        
            This method applies the given namespace to the store within the settings,
            facilitating task grouping or separation. It returns the current instance
            to support method chaining.
        
            Args:
                namespace: A string specifying the namespace to apply.
        
            Returns:
                Supertask: The current instance with the updated namespace configuration.
            """
        self.settings.store.with_namespace(namespace)
        return self

    def configure(self):
        """
        Configure the scheduler using store settings.
        
        Initializes a job store based on the address in the settings to support memory, PostgreSQL, or CrateDB. If pre_delete_jobs is enabled, it attempts to remove all existing jobs. Configures executor pools, job defaults, and sets the timezone to Europe/Vienna. Returns the instance for method chaining.
        
        Raises:
            RuntimeError: If the store address protocol is unrecognized.
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
        Set the HTTP server listening address.
        
        Configures the instance with the provided address for incoming HTTP requests.
        """
        self.listen_http = listen_http

    def start(self):
        """
        Starts the scheduler and HTTP service.
        
        Calls the methods to initialize the background scheduler and HTTP service,
        returning the current instance for method chaining.
        
        Returns:
            Supertask: The current instance.
        """
        self.start_scheduler()
        self.start_http_service()
        return self

    def start_scheduler(self):
        """
        Start the scheduler and log each job's next run time.
        
        This method initiates the background scheduler, retrieves all active jobs, and logs
        each job's identifier along with its next scheduled execution time. It returns the
        instance to allow for fluent method chaining.
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
        Keeps the application running until interrupted.
        
        This method enters an infinite loop to simulate ongoing application activity while
        displaying a waiting indicator and an exit prompt. It listens for keyboard or system
        interrupts, gracefully shuts down the scheduler upon receiving such a signal, and then
        returns the instance.
            
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
        Starts the HTTP service if a listening address is provided.
        
        If the instance's listen_http attribute is set, this method would normally initialize
        and start an HTTP service to handle incoming requests. Currently, the HTTP service logic
        is inactive and serves as a placeholder.
        
        Returns:
            The instance itself for method chaining.
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
        Executes a task's steps.
        
        Instantiates a Task using the provided keyword arguments and iterates over its steps.
        Steps with a false condition are skipped with a log entry. For steps using the
        "python-entrypoint", the corresponding function is dynamically loaded and invoked
        with the step's arguments, and the result is logged. A RuntimeError is raised if a step
        uses an unrecognized type.
            
        Raises:
            RuntimeError: If a task step has an unknown type.
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
