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
    """Return the relative path to the canonical YAML task file.
    
    This fixture provides the location of the YAML file at
    "examples/canonical/timetable.yaml", which defines the canonical task schedule
    for testing.
    """
    return "examples/canonical/timetable.yaml"


@pytest.fixture(scope="session")
def taskfile_yaml_url() -> str:
    """
    Return the URL of the canonical YAML task file on GitHub.
    
    Returns:
        str: A hard-coded URL pointing to the "timetable.yaml" file in the repository.
    """
    return "https://github.com/pyveci/supertask/raw/main/examples/canonical/timetable.yaml"
