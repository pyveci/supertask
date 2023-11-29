from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from datetime import datetime
import re

class CronJob(BaseModel):
    id: int
    crontab: str
    job: str
    enabled: bool
    last_run: Optional[Union[datetime, None]] = None
    last_status: Optional[Union[str, None]] = None

    #@validator('crontab') - it is more complex than this
    def validate_crontab(cls, v):
        pattern = r"(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5,7}"
        if not re.match(pattern, v):
            raise ValueError('Invalid crontab syntax')
        return v
