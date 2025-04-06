import datetime as dt
import logging
import os
import time

from apscheduler.schedulers.base import BaseScheduler
from icecream import ic
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .database import JsonResource

logger = logging.getLogger(__name__)


class JobSeeder:
    def __init__(self, source: str, scheduler: BaseScheduler, start_observer: bool = False):
        self.source = source
        self.scheduler = scheduler
        self.start_observer = start_observer

    def seed_jobs(self):
        logger.info(f"Seeding jobs from: {self.source}")
        # Initial load of jobs from cronjobs.json
        cronjobs = JsonResource(self.source).read()
        for cronjob in cronjobs:
            if cronjob.enabled:
                ic(cronjob)
                self.add_job(cronjob)
        return self

    def add_job(self, cronjob, reschedule=False):
        method = self.scheduler.add_job
        if reschedule:
            method = self.scheduler.reschedule_job
        cron_kwargs = cronjob.decode_crontab()
        method(
            cronjob.exec_python_ref,
            "cron",
            id=str(cronjob.id),
            jobstore="default",
            args=[cronjob.exec_args],
            max_instances=10,
            **cron_kwargs,
        )

    def start_filesystem_observer(self):
        logger.info("Starting filesystem observer")
        # Create an instance of FileChangeHandler with the scheduler
        file_change_handler = FileChangeHandler(seeder=self)

        # Watch cronjobs.json for changes in scheduled jobs
        observer = Observer()
        observer.schedule(file_change_handler, path=os.path.dirname(os.path.abspath(self.source)))
        observer.start()
        return self


# ruff: noqa: ERA001
class FileChangeHandler(FileSystemEventHandler):  # pragma: nocover
    def __init__(self, seeder: JobSeeder):
        self.seeder = seeder
        self.source = self.seeder.source
        self.scheduler = self.seeder.scheduler
        self.last_modified = time.time()

    def on_modified(self, event):
        if time.time() - self.last_modified < 1:
            return

        self.last_modified = time.time()

        if not event.is_directory and event.src_path.endswith(self.source):
            # Load jobs from cronjobs.json
            ic("FILE CHANGED")
            cronjobs = JsonResource(self.source).read()
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
                    self.seeder.add_job(cronjob)
                    next_run_time = job.trigger.get_next_fire_time(None, dt.datetime.now())
                    ic("ADDED: ", cronjob.job, next_run_time)

            # Reschedule existing jobs
            for cronjob in cronjobs:
                if cronjob.enabled:
                    # ic(cronjob.id)
                    self.seeder.add_job(cronjob, reschedule=True)
                    ic("RESCHED: ", cronjob.job, job.next_run_time)
