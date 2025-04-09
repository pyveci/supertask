from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from supertask.cli import cli


@pytest.fixture
def st_wait_noop(mocker):
    """
    Disables Supertask.run_forever to prevent infinite execution during tests.
    
    This fixture uses the provided mocker to patch the Supertask.run_forever method with a no-operation,
    ensuring that tests run without being blocked by an endless loop.
    """
    mocker.patch("supertask.core.Supertask.run_forever")


def test_cli_version(st_wait_noop):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="--version",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    assert "cli, version" in result.output


def test_cli_help(st_wait_noop):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="--help",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    assert "Options:" in result.output
    assert "SQLAlchemy URL of job store" in result.output


def test_cli_failure(st_wait_noop):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args=["--verbose", "run", "dummy.yaml"],
        catch_exceptions=False,
    )
    assert result.exit_code == 2, result.output

    assert "Error: Missing option '--store-address'." in result.output


def test_cli_storage_memory(st_wait_noop, taskfile_yaml):
    runner = CliRunner(env={"ST_STORE_ADDRESS": "memory://"})

    result = runner.invoke(
        cli,
        args=["--verbose", "run", taskfile_yaml],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output


@pytest.mark.skip("Currently defunct")
def test_cli_http_service(mocker, st_wait_noop):
    runner = CliRunner(env={"ST_STORE_ADDRESS": "memory://", "ST_HTTP_LISTEN_ADDRESS": "localhost:3333"})

    start_http_service_mock: MagicMock = mocker.patch("supertask.core.Supertask.start_http_service")
    result = runner.invoke(
        cli,
        args="--verbose",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    start_http_service_mock.assert_called_once_with("localhost:3333")
