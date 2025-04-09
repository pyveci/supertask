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
        Creates a JobStore instance from a given address.
        
        This class method initializes a new JobStore object using the provided
        database address.
        
        Args:
            address (str): The database address to initialize the JobStore.
        
        Returns:
            JobStore: A new JobStore instance configured with the specified address.
        """
        return cls(address=address)

    def with_namespace(self, namespace: str) -> "JobStore":
        """
        Sets the table name using the provided namespace.
        
        This method updates the JobStore object's table attribute by concatenating the NS_TABLE_PREFIX with the given namespace, and returns the updated instance for method chaining.
        
        Args:
            namespace: The namespace identifier appended to the prefix for the table name.
        
        Returns:
            The modified JobStore instance.
        """
        self.table = f"{self.NS_TABLE_PREFIX}{namespace}"
        return self

    def with_options(self, schema: t.Optional[str] = None, table: t.Optional[str] = None) -> "JobStore":
        """
        Update the job store's schema and table options.
        
        If a new schema or table name is provided, update the corresponding attribute on the
        job store instance and return the instance for method chaining.
        
        Args:
            schema: Optional new schema name. If not provided, the current schema remains unchanged.
            table: Optional new table name. If not provided, the current table remains unchanged.
        
        Returns:
            The job store instance with updated schema and/or table.
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
        Validate a crontab expression string.
        
        Checks that the provided cron expression matches a pattern with 5 to 7
        space-separated fields. Raises a ValueError if the expression does not
        conform to the expected format.
        
        Args:
            v (str): The cron expression string to validate.
        
        Returns:
            str: The validated cron expression.
            
        Raises:
            ValueError: If the cron expression fails to match the required pattern.
        """
        pattern = r"(((\d+,)+\d+|(\d+(\/|-)\d+)|\d+|\*) ?){5,7}"
        if not re.match(pattern, v):
            raise ValueError("Invalid crontab syntax")
        return v

    def crontab(self):
        """
        Parse a cron expression into its constituent time fields.
        
        This method accepts extended cron expressions that can include optional seconds and year
        fields. It supports expressions with 5, 6, or 7 space-separated components. For a 5-part
        expression (minute, hour, day, month, day_of_week), both seconds and year are set to None.
        For a 6-part expression (second, minute, hour, day, month, day_of_week), the year remains None.
        
        Raises:
            ValueError: If the cron expression does not consist of 5, 6, or 7 components.
        
        Returns:
            dict: A dictionary with keys 'second', 'minute', 'hour', 'day', 'month', 'day_of_week',
                  and 'year', representing the parsed components from the cron expression.
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
        Assign a namespace identifier if missing in metadata.
        
        After initialization, checks if the metadata dictionary lacks a valid namespace under the key
        defined by NAMESPACE_ATTRIBUTE and, if so, sets an ephemeral identifier using
        make_namespace_identifier(). The __context parameter is reserved for interface consistency and is not used.
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
        Generates an ephemeral namespace identifier.
        
        This method constructs an identifier by computing an MD5 hash of a string formed from the
        current host name, user name, and a resource value obtained from the instance metadata.
        If the resource value corresponds to an existing file path, its absolute path is used.
        """

        def digest(value):
            """
            Computes the MD5 hexadecimal digest of the input string.
            
            Encodes the string using UTF-8 and returns the hash as a hexadecimal string.
            
            Args:
                value: The string to be hashed.
            
            Returns:
                A hexadecimal string representing the MD5 digest of the input.
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
        Load a task or timetable definition from a JSON or YAML file.
        
        This method reads the specified file, parses its content based on the file
        extension, and embeds the source file identifier into the metadata using the
        class-specific SOURCE_ATTRIBUTE. JSON files must end with ".json" while YAML
        files require a ".yaml" or ".yml" extension. A NotImplementedError is raised if
        the file type is unsupported.
        
        Args:
            taskfile: Path to the task definition file.
        
        Returns:
            An instance of the class populated with data from the file.
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
        Calculates the job's duration in seconds.
        
        Computes the elapsed time between the job's start and end timestamps by subtracting the start 
        time from the end time and converting the resulting timedelta to seconds. Raises a RuntimeError 
        if the job has not finished (i.e., the end timestamp is not set).
        
        Returns:
            float: The duration of the job in seconds.
        """
        if not self.end:
            raise RuntimeError("Job has not finished yet")
        delta = self.end - self.start
        return self.delta_duration(delta)

    @property
    def elapsed(self) -> float:
        """
        Returns the elapsed time for the job in seconds.
        
        If the job's duration is available (typically when the job has completed), that
        value is returned. Otherwise, the elapsed time is computed as the difference
        between the current time and the job's start time, converted to seconds.
        """
        try:
            return self.duration
        except RuntimeError:
            delta = dt.datetime.now() - self.start
            return self.delta_duration(delta)

    @staticmethod
    def delta_duration(delta: dt.timedelta) -> float:
        """
        Convert a timedelta to its total duration in seconds.
        
        Calculates the complete duration represented by the given datetime.timedelta,
        including the fractional part of a second.
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
