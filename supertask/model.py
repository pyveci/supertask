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
        Creates a JobStore instance from the specified database address.
        
        Args:
            address: The database address to initialize the JobStore instance.
        
        Returns:
            A JobStore instance with its address set.
        """
        return cls(address=address)

    def with_namespace(self, namespace: str) -> "JobStore":
        """Sets the table name with a namespace.
        
        Updates the job store's table attribute by combining a predefined namespace
        prefix with the provided namespace identifier, and returns the modified instance.
        """
        self.table = f"{self.NS_TABLE_PREFIX}{namespace}"
        return self

    def with_options(self, schema: t.Optional[str] = None, table: t.Optional[str] = None) -> "JobStore":
        """
        Update the job store's schema and table attributes.
        
        If a non-null schema value is provided, the job store's schema is updated. Likewise, if a
        non-null table name is provided, the job store's table is updated. Returns the modified JobStore
        instance.
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
        Validates a cron expression against the expected crontab syntax.
        
        Checks if the provided cron expression matches a defined regex pattern and raises a ValueError if it does not.
        
        Args:
            v (str): The cron expression string to validate.
        
        Returns:
            str: The original cron expression if it is valid.
        """
        pattern = r"(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5,7}"
        if not re.match(pattern, v):
            raise ValueError("Invalid crontab syntax")
        return v

    def crontab(self):
        """
        Parse a crontab expression into its scheduling components.
        
        This method splits the crontab string (self.cron), which may contain 5, 6, or 7 fields:
        - A 5-field expression provides minute, hour, day, month, and day_of_week (with second and year set to None).
        - A 6-field expression includes a second field, leaving year as None.
        - A 7-field expression supplies both second and year.
        
        Returns:
            A dictionary with keys 'second', 'minute', 'hour', 'day', 'month', 'day_of_week', and 'year'.
            
        Raises:
            ValueError: If the cron expression does not match any of the expected field counts.
        
        Example:
            For the expression "*/10 * * * * * 2026", the method returns:
                {
                    'second': '*/10',
                    'minute': '*',
                    'hour': '*',
                    'day': '*',
                    'month': '*',
                    'day_of_week': '*',
                    'year': '2026'
                }.
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
        Ensure model metadata contains a valid namespace identifier.
        
        After initialization, this method verifies that the metadata includes a valid namespace
        identifier (under the key defined by NAMESPACE_ATTRIBUTE). If the identifier is missing or
        falsy, it generates an ephemeral identifier using make_namespace_identifier() and updates
        the metadata accordingly.
        
        Args:
            __context: Additional initialization context (unused).
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
        Generate a unique ephemeral namespace identifier.
        
        This method computes an MD5 hash of a string that combines the system's hostname,
        the current username, and a resource obtained from the instance's metadata using a
        predefined source attribute. If the resource is a valid file path, its absolute path
        is used to ensure a consistent identifier.
        
        Returns:
            str: A hexadecimal MD5 hash representing the namespace identifier.
        """

        def digest(value):
            """
            Generates the MD5 hexadecimal digest of a given string.
            
            Encodes the input using UTF-8 and computes its MD5 hash.
            
            Args:
                value: The string to be hashed.
            
            Returns:
                The hexadecimal MD5 digest of the input string.
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
        
        This class method opens and reads the specified file, parses its content based on the
        file extension, and instantiates an object with the loaded data. JSON files are handled
        using the JSON parser, while YAML files (with .yaml or .yml extensions) are processed using
        a YAML 1.2 compliant loader. The source file path is recorded in the metadata under the key
        defined by the class attribute SOURCE_ATTRIBUTE.
        
        Args:
            taskfile: The file path to the task definitions.
        
        Returns:
            An instance of the class populated with data from the file.
        
        Raises:
            NotImplementedError: If the file type is not supported.
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
        Returns the job's duration in seconds.
        
        Calculates the difference between the job's end and start times and converts it to seconds.
        Raises:
            RuntimeError: If the job has not finished (i.e., no end time is set).
        """
        if not self.end:
            raise RuntimeError("Job has not finished yet")
        delta = self.end - self.start
        return self.delta_duration(delta)

    @property
    def elapsed(self) -> float:
        """
        Return the elapsed time in seconds since the job started.
        
        If the duration property is available (indicating the job has completed), that value is returned.
        Otherwise, the elapsed time is calculated from the current time and the job's start time.
        """
        try:
            return self.duration
        except RuntimeError:
            delta = dt.datetime.now() - self.start
            return self.delta_duration(delta)

    @staticmethod
    def delta_duration(delta: dt.timedelta) -> float:
        """
        Convert a timedelta to the total number of seconds.
        
        Calculates the complete duration represented by the given timedelta as a float,
        including fractional seconds derived from its microseconds.
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
