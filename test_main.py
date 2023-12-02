import pytest
import sqlalchemy as sa

from main import run_supertask


def check_store(address: str):
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
def test_run_supertask(mocker, caplog, job_store_address):
    if not job_store_address.startswith("memory://"):
        check_store(job_store_address)
    mocker.patch("main.Supertask.start_http_service")
    run_supertask(job_store_address, pre_delete_jobs=True)
    assert "Configuring scheduler" in caplog.messages
    assert "Seeding jobs" in caplog.messages
    assert "Adding job tentatively -- it will be properly scheduled when the scheduler starts" in caplog.messages
    assert "Starting scheduler" in caplog.messages
    assert 'Added job "my_job" to job store "default"' in caplog.messages


def test_run_supertask_unknown():
    with pytest.raises(RuntimeError) as ex:
        run_supertask("foo://")
    assert ex.match("Initializing job store failed. Unknown address: foo://")
