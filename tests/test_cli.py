from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from supertask.cli import cli


@pytest.fixture
def st_wait_noop(mocker):
    mocker.patch("supertask.core.Supertask.wait")


def test_cli_version(st_wait_noop):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="--version",
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    assert "cli, version" in result.output


def test_cli_help(st_wait_noop):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="--help",
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    assert "Options:" in result.output
    assert "SQLAlchemy URL of job store" in result.output


def test_cli_failure(st_wait_noop):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="--verbose",
        catch_exceptions=False,
    )
    assert result.exit_code == 2

    assert "Error: Missing option '--store-address'." in result.output


def test_cli_storage_memory(st_wait_noop):
    runner = CliRunner(env={"ST_STORE_ADDRESS": "memory://"})

    result = runner.invoke(
        cli,
        args="--verbose",
        catch_exceptions=False,
    )
    assert result.exit_code == 0


def test_cli_http_service(mocker, st_wait_noop):
    runner = CliRunner(env={"ST_STORE_ADDRESS": "memory://", "ST_HTTP_LISTEN_ADDRESS": "localhost:3333"})

    start_http_service_mock: MagicMock = mocker.patch("supertask.core.Supertask.start_http_service")
    result = runner.invoke(
        cli,
        args="--verbose",
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    start_http_service_mock.assert_called_once_with("localhost:3333")
