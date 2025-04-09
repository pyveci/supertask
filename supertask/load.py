import datetime as dt
import logging
import time
import typing as t
from pathlib import Path

from apscheduler.schedulers.base import BaseScheduler
from icecream import ic
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from supertask.core import taskrunner
from supertask.model import Task, Timetable

logger = logging.getLogger(__name__)


class TimetableLoader:
    def __init__(self, scheduler: BaseScheduler, start_observer: bool = False):
        """
        Initializes a TimetableLoader with the specified scheduler.
        
        Validates the scheduler and configures whether to start the file observer.
        
        Args:
            scheduler: An instance of BaseScheduler used to schedule tasks.
            start_observer: If True, the file observer will be started immediately.
        
        Raises:
            ValueError: If the provided scheduler is None.
        """
        if scheduler is None:
            raise ValueError("Unable to use scheduler. Did you miss to invoke `supertask.configure()`?")
        self.scheduler = scheduler
        self.start_observer = start_observer

    def add(self, task: Task, reschedule=False):
        """
        Adds a scheduled job for the given task using its cron configuration.
        
        Iterates over each schedule defined in the task and, for cron schedules, extracts the
        trigger arguments and schedules the job using the taskrunner. If a schedule is not
        recognized as cron, a ValueError is raised.
        
        Args:
            task: Task object containing scheduling metadata and execution details.
            reschedule: Optional flag for rescheduling jobs; currently not used.
        
        Raises:
            ValueError: If a schedule is encountered that is not of a recognized cron type.
        """
        for schedule in task.on.schedule:
            if schedule.cron:
                trigger = "cron"
                trigger_args = schedule.crontab()
            else:
                raise ValueError(f"Unknown schedule type: {schedule}")
            self.scheduler.add_job(
                taskrunner.run,
                trigger=trigger,
                id=task.meta.id,
                name=task.meta.name,
                jobstore="default",
                # args=[cronjob.exec_args],
                kwargs=task.model_dump(by_alias=True),
                max_instances=10,
                replace_existing=True,
                **trigger_args,
            )

    def load(self, timetable: Timetable):
        """
        Loads enabled tasks from the given timetable.
        
        Iterates over each task in the timetable and, if the task is enabled, logs
        and adds it to the scheduler using the add() method. Returns the current
        instance for method chaining.
        """
        logger.info(f"Loading tasks from timetable. Source: {timetable}")
        for task in timetable.tasks:
            if task.meta.enabled:
                ic(task)
                self.add(task)
        return self

    def observe(self, timetable: Timetable):
        """
        Starts the filesystem observer for monitoring task file changes.
        
        Initializes a FileChangeHandler using the timetable's source file path and starts an observer
        to monitor changes in the parent directory of the specified file. Returns the loader instance.
          
        Args:
            timetable: Timetable containing scheduling metadata, including the source attribute that
                       specifies the task file location.
          
        Returns:
            The TimetableLoader instance (self) after starting the observer.
        """
        logger.info("Starting filesystem observer")
        # Create an instance of FileChangeHandler with the scheduler.
        source = Path(timetable.meta[Timetable.SOURCE_ATTRIBUTE])
        file_change_handler = FileChangeHandler(path=source, loader=self)

        # Watch for changes in task files.
        observer = Observer()
        observer.schedule(file_change_handler, path=str(source.parent))
        observer.start()
        return self


# ruff: noqa: ERA001
class FileChangeHandler(FileSystemEventHandler):  # pragma: nocover
    def __init__(self, path: Path, loader: TimetableLoader):
        """
        Initialize a file change handler.
        
        Stores the source file path and timetable loader, sets up the scheduler from the
        loader, and records the current time to control rapid successive file events.
        
        Args:
            path (Path): The file path to be monitored.
            loader (TimetableLoader): The loader instance managing task scheduling.
        """
        self.source = path
        self.loader = loader
        # self.source = self.seeder.source
        self.scheduler = self.loader.scheduler
        self.last_modified = time.time()

    def on_modified(self, event):
        """
        Handles file modification events to update scheduled cron jobs.
        
        Ignores events occurring within one second of the previous modification to prevent rapid re‐triggering.
        When the modified file matches the monitored source, this handler synchronizes the scheduler by
        removing obsolete jobs, adding new enabled jobs, and rescheduling existing enabled jobs.
        
        Args:
            event: The filesystem event that triggered the modification.
        """
        if time.time() - self.last_modified < 1:
            return

        self.last_modified = time.time()

        if not event.is_directory and event.src_path.endswith(str(self.source)):
            # Load jobs from cronjobs.json
            ic("FILE CHANGED")
            # cronjobs = JsonResource(self.source).read()
            cronjobs: t.List[t.Any] = []
            cronjob_ids = [str(cronjob.id) for cronjob in cronjobs]
            ic(cronjob_ids)

            # Get all existing jobs
            existing_jobs = self.scheduler.get_jobs()
            ic(existing_jobs)

            # Remove jobs that are not in cronjobs.json
            for job in existing_jobs:
                # ic("check-removale", job.id)
                if job.id not in cronjob_ids:
                    ic("REMOVE: ", job.id)
                    self.scheduler.remove_job(job.id)

            # Add jobs that are not in cronjobs.json
            for cronjob in cronjobs:
                # ic("check-add", cronjob.id)
                existing_job_ids = [job.id for job in existing_jobs]
                # ic(existing_job_ids)
                if cronjob.enabled and str(cronjob.id) not in existing_job_ids:
                    # ic("ADD: ", cronjob.id)
                    self.loader.add(cronjob)
                    next_run_time = job.trigger.get_next_fire_time(None, dt.datetime.now())
                    ic("ADDED: ", cronjob.job, next_run_time)

            # Reschedule existing jobs
            for cronjob in cronjobs:
                if cronjob.enabled:
                    # ic(cronjob.id)
                    self.loader.add(cronjob, reschedule=True)
                    ic("RESCHED: ", cronjob.job, job.next_run_time)
