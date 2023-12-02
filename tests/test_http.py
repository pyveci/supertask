from unittest import mock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from supertask.http.routes import router
from supertask.model import Settings

app = FastAPI()
app.include_router(router)

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def foo(cronjobs_json_file):
    # Inject settings as dependency to FastAPI. Thanks, @Mause.
    # https://github.com/tiangolo/fastapi/issues/2372#issuecomment-732492116
    app.dependency_overrides[Settings] = lambda: Settings(
        store_location=None, pre_delete_jobs=None, pre_seed_jobs=cronjobs_json_file
    )


@pytest.fixture
def write_noop(mocker):
    # Prevent _actually_ writing the `cronjobs.json` file.
    mocker.patch("supertask.provision.database.JsonResource.write")


def test_create_cronjob(write_noop):
    response = client.post("/cronjobs", data={"crontab": "* * * * *", "job": "foo", "enabled": "on"})
    assert response.status_code == 200
    assert response.json() == {
        "id": mock.ANY,
        "crontab": "* * * * *",
        "job": "foo",
        "enabled": True,
        "last_run": None,
        "last_status": None,
    }


def test_read_cronjobs():
    response = client.get("/cronjobs")
    assert response.status_code == 200
    assert response.json() == [
        {
            "crontab": "2-3,25 * * * *",
            "enabled": True,
            "id": 0,
            "job": "select * from testx",
            "last_run": None,
            "last_status": None,
        },
        {
            "crontab": "* * * * *",
            "enabled": True,
            "id": 1,
            "job": "job3",
            "last_run": None,
            "last_status": None,
        },
        {
            "crontab": "12-13,5,11 * * * *",
            "enabled": True,
            "id": 2,
            "job": "select 1",
            "last_run": None,
            "last_status": None,
        },
    ]


def test_read_cronjob():
    response = client.get("/cronjobs/2")
    assert response.status_code == 200
    assert response.json() == {
        "crontab": "12-13,5,11 * * * *",
        "enabled": True,
        "id": 2,
        "job": "select 1",
        "last_run": None,
        "last_status": None,
    }


@pytest.mark.skip("Does not work: <Response [422 Unprocessable Entity]>")
def test_update_cronjob(write_noop):
    response = client.put("/cronjobs/2", data={"id": "2", "crontab": "* * * * *", "job": "select 2", "enabled": "off"})
    assert response.status_code == 200
    assert response.json() == {
        "crontab": "12-13,5,11 * * * *",
        "enabled": True,
        "id": 2,
        "job": "select 1",
        "last_run": None,
        "last_status": None,
    }


def test_delete_cronjob(write_noop):
    response = client.delete("/cronjobs/2")
    assert response.status_code == 200
    assert response.json() == {
        "crontab": "12-13,5,11 * * * *",
        "enabled": True,
        "id": 2,
        "job": "select 1",
        "last_run": None,
        "last_status": None,
    }


def test_jobs_page():
    response = client.get("/")
    assert response.status_code == 200
    assert response.text.startswith("<!DOCTYPE html>")
    assert "<title>Supertask</title>" in response.text
