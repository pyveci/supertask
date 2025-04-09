import random
import time

from icecream import ic


def example_waiter(*args, **kwargs) -> float:
    """
    Simulates a workload with a randomized delay optionally adjusted by jitter.
    
    This function logs the job start time, computes a delay by generating a random number between 5 and 10 seconds
    and adding an optional jitter value, then pauses execution for the resulting duration. After waiting, it logs
    the job end information and returns a constant float value of 42.42.
    
    Keyword Args:
        jitter (int): Additional delay in seconds to add to the random value. Defaults to 0.
    
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
