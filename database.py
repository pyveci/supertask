import json
from models import CronJob

CRONJOBS_JSON = 'cronjobs.json'

# Sample data storex
cronjobs_db = []
# # Sample data store
# sample_cronjobs_data = [
#     {"cron": "*/5 * * * *", "job": "job1", "enabled": True},
#     {"cron": "0 * * * *", "job": "job2", "enabled": True},
#     {"cron": "*/15 * * * *", "job": "job3", "enabled": False},
# ]

# cronjobs_db = [CronJob(**cronjob) for cronjob in sample_cronjobs_data]

def get_db():
    with open(CRONJOBS_JSON, 'r') as f:
        cronjobs_data = json.load(f)
    for cronjob in cronjobs_data:
        if 'id' in cronjob:
            del cronjob['id']
    cronjobs_db = [CronJob(id=i, **cronjob) for i, cronjob in enumerate(cronjobs_data)]
    return cronjobs_db

def write_db(db):
    cronjobs_data = [cronjob.dict() for cronjob in db]
    with open(CRONJOBS_JSON, 'w') as f:
        json.dump(cronjobs_data, f)
