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
    """
    Returns the relative path to the canonical task YAML file.
    
    This function provides the file path for the timetable YAML file used in testing.
    """
    return "examples/canonical/timetable.yaml"


@pytest.fixture(scope="session")
def taskfile_yaml_url() -> str:
    """
    Return the URL for the canonical task YAML file.
    
    This fixture provides the URL to the remote YAML file hosted on GitHub, which is used
    to load task definitions for tests.
    """
    return "https://github.com/pyveci/supertask/raw/main/examples/canonical/timetable.yaml"
