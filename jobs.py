import random
import time

from icecream import ic


def my_job(job="select 1"):
    # Report about job start.
    start = time.strftime("%H:%M:%S", time.localtime())
    ic("JOB-START", job, start)

    # Emulate a computing workload.
    random_number = random.randint(5, 10)  # noqa: S311
    time.sleep(random_number)

    # Report about job end.
    result = random_number
    end = time.strftime("%H:%M:%S", time.localtime())
    ic("JOB-FINISH", job, start, end, result)
