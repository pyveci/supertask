import dataclasses
import re
import typing as t
from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel


@dataclasses.dataclass
class JobStoreLocation:
    """
    Manage the triple of database address, schema name, and table name.
    """

    address: str
    schema: str = "ext"
    table: str = "jobs"


class CronJob(BaseModel):
    """
    Mediate between JSON file and HTTP API.
    """

    id: int  # noqa: A003
    crontab: str
    job: str
    enabled: bool
    last_run: Optional[Union[datetime, None]] = None
    last_status: Optional[Union[str, None]] = None

    # @validator('crontab') - it is more complex than this
    def validate_crontab(cls, v):
        pattern = r"(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5,7}"
        if not re.match(pattern, v):
            raise ValueError("Invalid crontab syntax")
        return v


@dataclasses.dataclass
class Settings:
    """
    Bundle settings for propagating them from the environment to the FastAPI domain.
    """

    store_location: JobStoreLocation
    pre_delete_jobs: bool
    pre_seed_jobs: t.Optional[str]
