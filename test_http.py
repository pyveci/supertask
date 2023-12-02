from unittest import mock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from cronjob_routes import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)


@pytest.fixture
def write_noop(mocker):
    # Prevent _actually_ writing the `cronjobs.json` file.
    mocker.patch("database.write_db")
    mocker.patch("cronjob_routes.write_db")


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
            "enabled": False,
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
