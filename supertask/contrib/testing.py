import random
import time

from icecream import ic


def example_waiter(*args, **kwargs) -> float:
    """
    Simulates a workload with a random delay and logs job timing.
    
    This function logs the start and finish times of a job, pauses execution for a computed delay,
    and then returns a fixed float value. The delay is determined by generating a random number between
    5 and 10 seconds, then adding an optional jitter value specified in the keyword arguments. Any
    positional arguments are ignored.
    
    Args:
        **kwargs: Optional keyword arguments. May include a 'jitter' (int) representing additional
            seconds to add to the delay (default is 0).
    
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
