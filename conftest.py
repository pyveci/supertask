import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def prune_environment():
    delete_items = []
    for envvar in os.environ.keys():
        if envvar.startswith("ST_"):
            delete_items.append(envvar)
    for envvar in delete_items:
        del os.environ[envvar]


@pytest.fixture(scope="session")
def cronjobs_json_file() -> str:
    return "cronjobs.json"


@pytest.fixture(scope="session")
def cronjobs_json_url() -> str:
    return "https://github.com/WalBeh/scheduler-playground/raw/master/cronjobs.json"
