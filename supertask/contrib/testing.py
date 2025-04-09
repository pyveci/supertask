import random
import time

from icecream import ic


def example_waiter(*args, **kwargs) -> float:
    """
    Simulate a workload delay with optional jitter.
    
    Logs the start time, computes a delay time by generating a random duration between 5 and 10
    seconds augmented by an optional jitter value, pauses execution for that duration, logs the
    finish details, and returns a fixed result.
    
    Args:
        jitter (int, optional): Extra seconds added to the delay. Defaults to 0.
    
    Returns:
        float: The constant value 42.42.
    """
    jitter = kwargs.pop("jitter", 0)

    # Report about job start.
    start = time.strftime("%H:%M:%S", time.localtime())
    ic("JOB-START", start)

    # Emulate a computing workload.
    random_number = random.randint(5, 10) + jitter  # noqa: S311
    ic(f"PAYLOAD: {random_number} seconds, {jitter} jitter")
    time.sleep(random_number)

    # Report about job end.
    result = random_number
    end = time.strftime("%H:%M:%S", time.localtime())
    print()  # noqa: T201
    ic("JOB-FINISH", start, end, result)

    return 42.42
