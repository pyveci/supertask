import dataclasses
import datetime as dt
import getpass
import hashlib
import json
import logging
import os
import re
import socket
import typing as t
from pathlib import Path

import yaml
import yamlcore
from pueblo.io import to_io
from pydantic import BaseModel, Field

from supertask.util import read_inline_script_metadata

logger = logging.getLogger(__name__)


ScalarType = t.Union[str, int, float]


@dataclasses.dataclass
class JobStore:
    """
    Manage the triple of database address, schema name, and table name.
    """

    address: str
    schema: str = "supertask"
    table: str = "jobs"

    NS_TABLE_PREFIX: t.ClassVar[str] = "ap_"

    @classmethod
    def from_address(cls, address: str) -> "JobStore":
        return cls(address=address)

    def with_namespace(self, namespace: str) -> "JobStore":
        self.table = f"{self.NS_TABLE_PREFIX}{namespace}"
        return self

    def with_options(self, schema: t.Optional[str] = None, table: t.Optional[str] = None) -> "JobStore":
        if schema:
            self.schema = schema
        if table:
            self.table = table
        return self


class TaskMetadata(BaseModel):
    """Manage the tasks' metadata."""

    id: str
    name: str
    description: str
    enabled: bool

    # last_run: Optional[Union[datetime, None]] = None  # noqa: ERA001
    # last_status: Optional[Union[str, None]] = None  # noqa: ERA001


class ScheduleItem(BaseModel):
    """Manage information about the schedule of an item."""

    cron: str

    # TODO: Enable validation. Hint: It is more complex than this.
    # @validator('cron')
    def validate_cron(cls, v):
        pattern = r"(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5,7}"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid crontab syntax")
        return v

    def crontab(self):
        """
        Extended crontab expressions, including sub-minute resolutions and year constraints.
        It is a 7-tuple, while traditionally it's only 5 components. Example:

            Humanized: Every 10 seconds, only in 2026.
            Expression: */10 * * * * * 2026

        -- https://crontabkit.com/crontab-every-10-seconds
        """
        second, minute, hour, day, month, day_of_week, year = [None] * 7
        try:
            second, minute, hour, day, month, day_of_week, year = self.cron.split()
        except ValueError:
            try:
                second, minute, hour, day, month, day_of_week = self.cron.split()
            except ValueError:
                try:
                    minute, hour, day, month, day_of_week = self.cron.split()
                except ValueError as ex:
                    raise ValueError(f"Invalid crontab syntax: {self.cron}") from ex
        return dict(  # noqa: C408
            second=second,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            year=year,
        )


class Event(BaseModel):
    """Manage information about different kinds of trigger events."""

    schedule: t.List[ScheduleItem]


class Step(BaseModel):
    """Manage information about task steps."""

    name: str
    uses: str
    run: str
    args: t.List[ScalarType] = Field(default_factory=list)
    kwargs: t.Dict[str, t.Any] = Field(default_factory=dict)
    if_: bool = Field(alias="if", default=True)


class Task(BaseModel):
    """Manage information about a whole task."""

    meta: TaskMetadata
    on: Event
    steps: t.List[Step]


class Timetable(BaseModel):
    """
    Manage information about a whole timetable, including multiple task definitions.
    """

    meta: t.Dict[str, t.Any] = Field(default_factory=dict)
    tasks: t.List[Task] = Field(default_factory=list)

    NAMESPACE_ATTRIBUTE: t.ClassVar = "namespace"
    SOURCE_ATTRIBUTE: t.ClassVar = "taskfile"

    def model_post_init(self, __context: t.Any) -> None:
        """
        Adjust the model after initialization.
        """
        # If the timetable file or resource does not provide a namespace identifier, provide an ephemeral one.
        if self.NAMESPACE_ATTRIBUTE not in self.meta or not self.meta[self.NAMESPACE_ATTRIBUTE]:
            self.meta[self.NAMESPACE_ATTRIBUTE] = self.make_namespace_identifier()

    @property
    def namespace(self) -> str:
        """
        Return the namespace identifier.
        """
        return self.meta[self.NAMESPACE_ATTRIBUTE]

    def make_namespace_identifier(self):
        """
        Provide an ephemeral namespace identifier when needed.
        """

        def digest(value):
            return hashlib.md5(value.encode()).hexdigest()  # noqa: S324

        hostname = socket.gethostname()
        username = getpass.getuser()
        resource = self.meta.get(self.SOURCE_ATTRIBUTE, "global")
        if Path(resource).exists():
            resource = str(Path(resource).absolute())
        return digest(f"{hostname}-{username}-{resource}")

    @classmethod
    def load(cls, taskfile: str):
        """
        Load task definitions from a file or resource.
        """
        logger.info(f"Loading task(s) from file. Source: {taskfile}")

        with to_io(taskfile, "r") as f:
            if taskfile.endswith(".json"):
                data = json.load(f)
            elif taskfile.endswith(".yaml") or taskfile.endswith(".yml"):
                # Use YAML 1.2 compliant loading, otherwise "on" will be translated to `True`, for example.
                data = yaml.load(f, Loader=yamlcore.CoreLoader)  # noqa: S506
            elif taskfile.endswith(".py"):
                return cls.from_python(taskfile)
            else:
                raise NotImplementedError(f"Task or timetable file type not supported: {taskfile}")
            data["meta"][cls.SOURCE_ATTRIBUTE] = taskfile
            return cls(**data)

    @classmethod
    def from_python(cls, pythonfile: str):
        tt = cls()
        pythonfile_path = Path(pythonfile)
        tt.meta[cls.SOURCE_ATTRIBUTE] = pythonfile
        task_data = read_inline_script_metadata("task", pythonfile_path.read_text())
        os.environ.update(task_data.get("env", {}))
        tt.tasks.append(
            Task(
                meta=TaskMetadata(id="python", name=pythonfile_path.stem, description="TODO", enabled=True),
                on=Event(schedule=[ScheduleItem(cron=task_data["cron"])]),
                steps=[
                    Step(
                        name=pythonfile_path.stem,
                        uses="python-file",
                        run=f"{pythonfile_path}:run",
                        args=[],
                        kwargs=task_data.get("options", {}),
                    ),
                ],
            )
        )
        return tt


class CronJob(BaseModel):
    """
    Manage information about a job, which is effectively task + runtime information.
    """

    task: Task
    start: dt.datetime = Field(default_factory=dt.datetime.now)
    end: t.Optional[dt.datetime]

    @property
    def duration(self) -> float:
        """
        Duration in seconds if the job has finished.
        """
        if not self.end:
            raise RuntimeError("Job has not finished yet")
        delta = self.end - self.start
        return self.delta_duration(delta)

    @property
    def elapsed(self) -> float:
        """
        Elapsed time in seconds.
        """
        try:
            return self.duration
        except RuntimeError:
            delta = dt.datetime.now() - self.start
            return self.delta_duration(delta)

    @staticmethod
    def delta_duration(delta: dt.timedelta) -> float:
        """Convert dt.timedelta to seconds."""
        return delta.total_seconds()


@dataclasses.dataclass
class Settings:
    """
    Bundle settings for propagating them from the environment to the FastAPI domain.
    """

    store: JobStore
    pre_delete_jobs: bool
