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
def taskfile_yaml() -> str:
    return "examples/canonical/timetable.yaml"


@pytest.fixture(scope="session")
def taskfile_yaml_url() -> str:
    return "https://github.com/pyveci/supertask/raw/main/examples/canonical/timetable.yaml"


@pytest.fixture(scope="session")
def taskfile_python() -> str:
    return "examples/minimal/hellodb.py"
