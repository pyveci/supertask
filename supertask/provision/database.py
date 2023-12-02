import json
import typing as t

from pueblo.io import to_io

from supertask.model import CronJob

# Sample data storex
cronjobs_db: t.List[CronJob] = []


"""
# Sample data store
sample_cronjobs_data = [
    {"cron": "*/5 * * * *", "job": "job1", "enabled": True},
    {"cron": "0 * * * *", "job": "job2", "enabled": True},
    {"cron": "*/15 * * * *", "job": "job3", "enabled": False},
]

cronjobs_db = [CronJob(**cronjob) for cronjob in sample_cronjobs_data]
"""


class JsonResource:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def read_index(self):
        with open(self.filepath, "r") as f:
            cronjobs_data = json.load(f)
        return [CronJob(**job) for job in cronjobs_data]

    def read(self):
        with to_io(self.filepath, "r") as f:
            cronjobs_data = json.load(f)
        for cronjob in cronjobs_data:
            if "id" in cronjob:
                del cronjob["id"]
        cronjobs_db = [CronJob(id=i, **cronjob) for i, cronjob in enumerate(cronjobs_data)]
        return cronjobs_db

    def write(self, db):
        cronjobs_data = [cronjob.dict() for cronjob in db]
        with open(self.filepath, "w") as f:
            json.dump(cronjobs_data, f)
