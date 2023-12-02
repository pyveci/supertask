import datetime as dt
import logging
from unittest import mock

import pytest
import sqlalchemy as sa
from cratedb_toolkit.util import DatabaseAdapter

from core import Supertask
from job_seeder import JobSeeder

logger = logging.getLogger(__name__)


def check_store(address: str):
    if address.startswith("memory://"):
        return
    engine: sa.engine.Engine = sa.create_engine(url=address)
    try:
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1;"))
    except sa.exc.OperationalError as ex:
        if "No more Servers available" in str(ex):
            raise pytest.skip(f"Skipping test case, because job store is not available: {address}") from ex


@pytest.mark.parametrize(
    "job_store_address", ["memory://", "postgresql://postgres:postgres@localhost", "crate://crate@localhost"]
)
def test_supertask_stores_seeded(caplog, job_store_address):
    check_store(job_store_address)

    st = Supertask(job_store_address=job_store_address, pre_delete_jobs=True)
    js = JobSeeder(scheduler=st.scheduler)
    js.seed_jobs()
    st.start()

    assert "Configuring scheduler" in caplog.messages
    assert "Seeding jobs" in caplog.messages
    assert "Adding job tentatively -- it will be properly scheduled when the scheduler starts" in caplog.messages
    assert "Starting scheduler" in caplog.messages
    assert 'Added job "my_job" to job store "default"' in caplog.messages


def dummy_job(param1: str):
    pass


def test_supertask_cratedb_store(caplog):
    # Create a job using Supertask.
    job_store_address = "crate://crate@localhost/"
    check_store(job_store_address)
    st = Supertask(job_store_address, pre_delete_jobs=True)
    reference_time = dt.datetime(year=8022, month=1, day=1, tzinfo=dt.timezone.utc)
    st.scheduler.add_job(
        dummy_job, args=["something"], trigger="interval", id="foo", name="bar", next_run_time=reference_time
    )
    st.start()

    # Verify the job has been stored into CrateDB.
    cratedb = DatabaseAdapter(dburi=job_store_address)
    assert cratedb.table_exists("ext.jobs")
    assert cratedb.count_records("ext.jobs") == 1
    assert cratedb.run_sql("SELECT * FROM ext.jobs", records=True) == [
        {"id": "foo", "job_state": mock.ANY, "next_run_time": reference_time.timestamp()}
    ]


def test_supertask_unknown_store():
    with pytest.raises(RuntimeError) as ex:
        Supertask("foo://")
    assert ex.match("Initializing job store failed. Unknown address: foo://")
