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
    schema: str = "supertask"
    table: str = "jobs"


class CronJob(BaseModel):
    """
    Mediate between JSON file and HTTP API.
    """

    id: int  # noqa: A003
    name: str
    trigger_cron: str
    exec_python_ref: Optional[str] = None
    exec_args: Optional[t.List[str]] = None
    exec_sql: Optional[str] = None
    enabled: Optional[bool] = False
    last_run: Optional[Union[datetime, None]] = None
    last_status: Optional[Union[str, None]] = None

    def model_post_init(self, __context: t.Any) -> None:
        self.exec_args = self.exec_args or []

    # @validator('trigger_cron') - it is more complex than this
    def validate_crontab(cls, v):
        pattern = r"(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5,7}"
        if not re.match(pattern, v):
            raise ValueError("Invalid crontab syntax")
        return v

    def decode_crontab(self):
        """
        Extended crontab expressions, including sub-minute resolutions and year constraints.
        It is a 7-tuple, while traditionally it's only 5 components. Example:

            Humanized:  Every 10 seconds, only in 2026.
            Expression: */10 * * * * * 2026

        -- https://crontabkit.com/crontab-every-10-seconds
        """
        second, minute, hour, day, month, day_of_week, year = [None] * 7
        try:
            second, minute, hour, day, month, day_of_week, year = self.trigger_cron.split()
        except ValueError:
            try:
                second, minute, hour, day, month, day_of_week = self.trigger_cron.split()
            except ValueError:
                try:
                    minute, hour, day, month, day_of_week = self.trigger_cron.split()
                except ValueError as ex:
                    raise ValueError(f"Invalid crontab syntax: {self.trigger_cron}") from ex
        return dict(  # noqa: C408
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            year=year,
        )


@dataclasses.dataclass
class Settings:
    """
    Bundle settings for propagating them from the environment to the FastAPI domain.
    """

    store_location: JobStoreLocation
    pre_delete_jobs: bool
    pre_seed_jobs: t.Optional[str]
