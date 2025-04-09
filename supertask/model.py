import dataclasses
import datetime as dt
import getpass
import hashlib
import json
import logging
import re
import socket
import typing as t
from pathlib import Path

import yaml
import yamlcore
from pueblo.io import to_io
from pydantic import BaseModel, Field

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
        """
        Creates a new JobStore instance from a database address.
        
        Initializes and returns a JobStore using the provided address string for job storage.
        
        Args:
            address: A string representing the database address used for job storage.
        
        Returns:
            A JobStore instance configured with the specified address.
        """
        return cls(address=address)

    def with_namespace(self, namespace: str) -> "JobStore":
        """
        Update the table attribute with the specified namespace and return the JobStore instance.
        
        Args:
            namespace: Namespace to be appended to the table prefix for forming the table name.
        
        Returns:
            The JobStore instance with its table attribute updated.
        """
        self.table = f"{self.NS_TABLE_PREFIX}{namespace}"
        return self

    def with_options(self, schema: t.Optional[str] = None, table: t.Optional[str] = None) -> "JobStore":
        """
        Updates the JobStore's schema and table options.
        
        If provided, new schema and table names are applied to the instance, while any 
        parameter left as None remains unchanged.
        
        Args:
            schema: Optional new schema name.
            table: Optional new table name.
        
        Returns:
            The JobStore instance with updated options.
        """
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
        """
        Validate a cron expression string.
        
        Checks whether the provided cron expression matches the expected crontab syntax,
        requiring five to seven fields. Raises a ValueError if the expression does not conform
        to the pattern.
        
        Parameters:
            v (str): The cron expression to validate.
        
        Returns:
            str: The valid cron expression.
            
        Raises:
            ValueError: If the cron expression is invalid.
        """
        pattern = r"(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5,7}"
        if not re.match(pattern, v):
            raise ValueError("Invalid crontab syntax")
        return v

    def crontab(self):
        """
        Parses an extended crontab expression with optional seconds and year.
        
        This method splits the crontab string stored in `self.cron` into its constituent
        parts: second, minute, hour, day, month, day_of_week, and year. It supports the
        traditional 5-part format as well as extended 6-part (including seconds) and
        7-part (including seconds and year) formats, setting missing fields to None.
        A ValueError is raised if the expression cannot be parsed as any supported format.
        
        Example:
            For a schedule of "*/10 * * * * * 2026", the returned dictionary will be:
            
                {
                    "second": "*/10",
                    "minute": "*",
                    "hour": "*",
                    "day": "*",
                    "month": "*",
                    "day_of_week": "*",
                    "year": "2026"
                }
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
    kwargs: t.Dict[str, ScalarType] = Field(default_factory=dict)
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

    meta: t.Dict[str, t.Any]
    tasks: t.List[Task]

    NAMESPACE_ATTRIBUTE: t.ClassVar = "namespace"
    SOURCE_ATTRIBUTE: t.ClassVar = "taskfile"

    def model_post_init(self, __context: t.Any) -> None:
        """
        Adjust the model after initialization.
        
        Ensures the model's metadata contains a valid namespace identifier. If the
        NAMESPACE_ATTRIBUTE is missing or falsy in meta, an ephemeral namespace identifier
        is generated via make_namespace_identifier(). The __context parameter is reserved
        for future use and is currently ignored.
        """
        # If the timetable file or resource does not provide a namespace identifier, provide an ephemeral one.
        if self.NAMESPACE_ATTRIBUTE not in self.meta or not self.meta[self.NAMESPACE_ATTRIBUTE]:
            self.meta[self.NAMESPACE_ATTRIBUTE] = self.make_namespace_identifier()

    @property
    def namespace(self) -> str:
        """
        Retrieves the namespace identifier from the metadata.
        
        Returns:
            str: The namespace identifier extracted from the metadata using the key stored in NAMESPACE_ATTRIBUTE.
        """
        return self.meta[self.NAMESPACE_ATTRIBUTE]

    def make_namespace_identifier(self):
        """
        Generates an ephemeral namespace identifier.
        
        Combines the system's host name, the current user's name, and a resource value from the object's
        metadata to create a unique identifier. If the resource corresponds to an existing file, its absolute
        path is used; otherwise, "global" is substituted. The resulting string is hashed using MD5 to produce
        a 32-character hexadecimal digest.
        
        Returns:
            str: The computed namespace identifier.
        """

        def digest(value):
            """
            Computes the MD5 hexadecimal digest of the given string.
            
            The input is encoded using UTF-8 before computing the MD5 hash, and the
            resulting digest is returned as a 32-character hexadecimal string.
            
            Args:
                value: The string to hash.
            
            Returns:
                The MD5 digest of the input as a hexadecimal string.
            """
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
        Load task definitions from a JSON or YAML file.
        
        This class method reads a file containing task definitions and returns a new instance
        of the class populated with the file's content. If the file extension is '.json', the
        file is parsed as JSON; if it is '.yaml' or '.yml', it is parsed as YAML using a YAML 1.2
        compliant loader. The method also records the source file path in the task metadata 
        using the attribute defined by SOURCE_ATTRIBUTE.
        
        Args:
            taskfile: The path to the task definition file.
        
        Returns:
            An instance of the class initialized with the loaded task definitions.
        
        Raises:
            NotImplementedError: If the file extension is not supported.
        """
        logger.info(f"Loading task(s) from file. Source: {taskfile}")

        with to_io(taskfile, "r") as f:
            if taskfile.endswith(".json"):
                data = json.load(f)
            elif taskfile.endswith(".yaml") or taskfile.endswith(".yml"):
                # Use YAML 1.2 compliant loading, otherwise "on" will be translated to `True`, for example.
                data = yaml.load(f, Loader=yamlcore.CoreLoader)  # noqa: S506
            else:
                raise NotImplementedError(f"Task or timetable file type not supported: {taskfile}")
            data.setdefault("meta", {})
            data["meta"][cls.SOURCE_ATTRIBUTE] = taskfile
            return cls(**data)


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
        Return the job's duration in seconds.
        
        Calculates the elapsed time between the job's start and end times by subtracting the start time from the end time and converting the result to seconds. Raises a RuntimeError if the job has not finished (i.e., if the end time is not set).
        
        Returns:
            float: The duration in seconds.
        """
        if not self.end:
            raise RuntimeError("Job has not finished yet")
        delta = self.end - self.start
        return self.delta_duration(delta)

    @property
    def elapsed(self) -> float:
        """
        Return the elapsed job time in seconds.
        
        If the job's total duration is already set, it is returned. Otherwise, if accessing the
        duration raises a RuntimeError (indicating that the job is still running), the elapsed time is
        calculated as the difference between the current time and the job's start time.
        
        Returns:
            float: The elapsed time of the job in seconds.
        """
        try:
            return self.duration
        except RuntimeError:
            delta = dt.datetime.now() - self.start
            return self.delta_duration(delta)

    @staticmethod
    def delta_duration(delta: dt.timedelta) -> float:
        """Return the total duration in seconds from a timedelta.
        
        Converts a datetime.timedelta object into a float representing the full duration
        in seconds, including the fractional microsecond part.
        """
        return delta.total_seconds() + (delta.microseconds / 1_000_000)


@dataclasses.dataclass
class Settings:
    """
    Bundle settings for propagating them from the environment to the FastAPI domain.
    """

    store: JobStore
    pre_delete_jobs: bool
    pre_seed_jobs: t.Optional[str]
