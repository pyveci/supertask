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
    Returns the file path for the canonical YAML taskfile.
    
    This function returns a constant string that specifies the relative path to the
    YAML file used for testing from the examples/canonical directory.
    """
    return "examples/canonical/timetable.yaml"


@pytest.fixture(scope="session")
def taskfile_yaml_url() -> str:
    """
    Return the URL to the canonical timetable YAML file.
    
    Returns:
        str: A GitHub URL referencing the timetable YAML file used for testing.
    """
    return "https://github.com/pyveci/supertask/raw/main/examples/canonical/timetable.yaml"
