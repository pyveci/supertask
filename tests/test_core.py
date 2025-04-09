import datetime as dt
import logging
from unittest import mock

import pytest
import sqlalchemy as sa
from cratedb_toolkit.util import DatabaseAdapter

from supertask.core import Supertask
from supertask.load import TimetableLoader
from supertask.model import JobStore, Timetable

logger = logging.getLogger(__name__)


def check_store(address: str):
    if address.startswith("memory://"):
        return
    engine: sa.engine.Engine = sa.create_engine(url=address)
    try:
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1;"))
    except sa.exc.OperationalError as ex:
        msg = str(ex)
        if "No more Servers available" in msg or "Connection refused" in msg:
            raise pytest.skip(f"Skipping test case, because job store is not available: {address}") from ex


@pytest.mark.parametrize(
    "job_store_address",
    ["memory://", "postgresql://postgres:postgres@localhost:5433", "crate://crate@localhost/?schema=testdrive"],
)
def test_supertask_stores_seeded_file(caplog, job_store_address, taskfile_yaml):
    check_store(job_store_address)

    st = Supertask(store=job_store_address, pre_delete_jobs=True, pre_seed_jobs=taskfile_yaml).configure()
    tt = Timetable.load(taskfile_yaml)
    TimetableLoader(scheduler=st.scheduler).load(tt)
    st.start()

    assert "Configuring scheduler" in caplog.messages
    assert "Loading task(s) from file. Source: examples/canonical/timetable.yaml" in caplog.text
    assert "Adding job tentatively -- it will be properly scheduled when the scheduler starts" in caplog.messages
    assert "Starting scheduler" in caplog.messages
    assert 'Added job "Example Python reference" to job store "default"' in caplog.messages


@pytest.mark.skip(reason="Does not work when job representation changes")
@pytest.mark.parametrize(
    "job_store_address",
    ["memory://", "postgresql://postgres:postgres@localhost:5433", "crate://crate@localhost/?schema=testdrive"],
)
def test_supertask_stores_seeded_url(caplog, job_store_address, taskfile_yaml_url):
    check_store(job_store_address)

    st = Supertask(store=job_store_address, pre_delete_jobs=True, pre_seed_jobs=taskfile_yaml_url)
    js = TimetableLoader(source=taskfile_yaml_url, scheduler=st.scheduler)
    js.load()
    st.start()

    assert "Configuring scheduler" in caplog.messages
    assert "Loading task(s) from file. Source: examples/canonical/timetable.yaml" in caplog.text
    assert "Adding job tentatively -- it will be properly scheduled when the scheduler starts" in caplog.messages
    assert "Starting scheduler" in caplog.messages
    assert 'Added job "Example Python reference" to job store "default"' in caplog.messages


def dummy_job(param1: str):
    """
    A placeholder job function for scheduler tests.
    
    This function is used as a no-operation stub for simulating a scheduled job.
    It accepts a single parameter to conform to job signatures but performs no actions.
    
    Args:
        param1 (str): A dummy parameter for testing purposes.
    """
    pass


def test_supertask_cratedb_store(caplog):
    # Create a job using Supertask.
    """
    Test that a scheduled job is correctly persisted in a CrateDB job store.
    
    This test sets up a CrateDB job store using Supertask, schedules a dummy job with a specified future
    run time, and verifies that the job record is properly inserted into the designated schema and table.
    """
    job_store_address = "crate://crate@localhost/"
    check_store(job_store_address)
    st = Supertask(JobStore(address=job_store_address, schema="testdrive"), pre_delete_jobs=True).configure()
    reference_time = dt.datetime(year=8022, month=1, day=1, tzinfo=dt.timezone.utc)
    st.scheduler.add_job(
        dummy_job, args=["something"], trigger="interval", id="foo", name="bar", next_run_time=reference_time
    )
    st.start()

    # Verify the job has been stored into CrateDB.
    cratedb = DatabaseAdapter(dburi=job_store_address)
    assert cratedb.table_exists("testdrive.jobs")
    assert cratedb.count_records("testdrive.jobs") == 1
    assert cratedb.run_sql("SELECT * FROM testdrive.jobs", records=True) == [
        {"id": "foo", "job_state": mock.ANY, "next_run_time": reference_time.timestamp()}
    ]


def test_supertask_cratedb_custom_schema_and_table(caplog):
    # Create a job using Supertask.
    job_store_address = "crate://crate@localhost/"
    check_store(job_store_address)
    store_location = JobStore(
        address=job_store_address,
        schema="testdrive",
        table="bar",
    )
    st = Supertask(store_location, pre_delete_jobs=True).configure()
    reference_time = dt.datetime(year=8022, month=1, day=1, tzinfo=dt.timezone.utc)
    st.scheduler.add_job(
        dummy_job, args=["something"], trigger="interval", id="foo", name="bar", next_run_time=reference_time
    )
    st.start()

    # Verify the job has been stored into CrateDB.
    cratedb = DatabaseAdapter(dburi=job_store_address)
    assert cratedb.table_exists("testdrive.bar")
    assert cratedb.count_records("testdrive.bar") == 1
    assert cratedb.run_sql("SELECT * FROM testdrive.bar", records=True) == [
        {"id": "foo", "job_state": mock.ANY, "next_run_time": reference_time.timestamp()}
    ]


def test_supertask_unknown_store():
    with pytest.raises(RuntimeError) as ex:
        Supertask("foo://").configure()
    assert ex.match("Initializing job store failed. Unknown address: foo://")
