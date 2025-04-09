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
        Initializes a TimetableLoader instance with the provided scheduler and observer option.
        
        Args:
            scheduler: A BaseScheduler instance for managing tasks; must not be None.
            start_observer: If True, starts the filesystem observer for task file changes.
        
        Raises:
            ValueError: If the scheduler argument is None.
        """
        if scheduler is None:
            raise ValueError("Unable to use scheduler. Did you miss to invoke `supertask.configure()`?")
        self.scheduler = scheduler
        self.start_observer = start_observer

    def add(self, task: Task, reschedule=False):
        """
        Schedules a task using its cron schedule.
        
        Iterates over each schedule defined in the task and, for cron schedules, computes the 
        trigger arguments via the schedule’s crontab() method and adds a corresponding job to 
        the scheduler using taskrunner.run as the callable. If a schedule is not of cron type, 
        a ValueError is raised.
        
        Note:
          The 'reschedule' flag is currently unused as the job is always added with 
          replace_existing=True.
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
        Loads enabled tasks from the given timetable and schedules them.
        
        This method logs the timetable source, iterates over each task in the timetable,
        and for every task that is enabled (according to its metadata), it passes the task
        to the scheduler by calling the add method.
        
        Parameters:
            timetable (Timetable): The timetable containing the tasks to be scheduled.
        
        Returns:
            TimetableLoader: The loader instance with the tasks loaded.
        """
        logger.info(f"Loading tasks from timetable. Source: {timetable}")
        for task in timetable.tasks:
            if task.meta.enabled:
                ic(task)
                self.add(task)
        return self

    def observe(self, timetable: Timetable):
        """
        Starts a filesystem observer to monitor task file changes.
        
        Extracts the source file path from the timetable's metadata using the defined source
        attribute, sets up a FileChangeHandler for file modifications, and registers an observer
        to monitor the parent directory. The observer is started immediately, and the current
        instance is returned.
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
        Initialize a FileChangeHandler for monitoring file changes.
        
        Sets the source path to be observed, associates the provided timetable loader
        (from which the scheduler is derived), and records the current time to prevent
        rapid successive event handling.
        
        Args:
            path: Filesystem path to monitor for modifications.
            loader: TimetableLoader instance managing task scheduling.
        """
        self.source = path
        self.loader = loader
        # self.source = self.seeder.source
        self.scheduler = self.loader.scheduler
        self.last_modified = time.time()

    def on_modified(self, event):
        """
        Handles file modification events to refresh scheduled cron jobs.
        
        If triggered less than one second after the previous event, no action is taken. When a modified event is detected on a non-directory file matching the monitored source, the function:
          - Retrieves the current scheduled jobs.
          - Removes jobs that are no longer defined in the external cron configuration.
          - Adds new enabled cron jobs that are not already scheduled.
          - Reschedules existing enabled jobs.
        
        Parameters:
            event: A filesystem event with attributes 'is_directory' and 'src_path'.
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
