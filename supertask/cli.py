import click
from dotenv import find_dotenv, load_dotenv

from supertask.core import Supertask
from supertask.load import TimetableLoader
from supertask.model import JobStore, Timetable
from supertask.util import setup_logging

# TODO: Gate behind an environment variable?
load_dotenv(find_dotenv())


@click.group()
@click.option("--store-address", envvar="ST_STORE_ADDRESS", type=str, required=True, help="SQLAlchemy URL of job store")
@click.option(
    "--store-schema-name", envvar="ST_STORE_SCHEMA_NAME", type=str, required=False, help="Job store database schema"
)
@click.option(
    "--store-table-name", envvar="ST_STORE_TABLE_NAME", type=str, required=False, help="Job store database table"
)
@click.option(
    "--pre-delete-jobs", envvar="ST_JOBS_DELETE", is_flag=True, required=False, help="Prune job store before starting"
)
@click.option(
    "--http-listen-address",
    envvar="ST_HTTP_LISTEN_ADDRESS",
    type=str,
    default="localhost:4243",
    required=False,
    help="HTTP API service listen address",
)
@click.option("--verbose", is_flag=True, required=False, default=True, help="Turn logging on/off")
@click.option("--debug", is_flag=True, required=False, help="Turn on logging with debug level")
@click.version_option()
@click.pass_context
def cli(
    ctx: click.Context,
    store_address: str,
    store_schema_name: str,
    store_table_name: str,
    pre_delete_jobs: bool,
    http_listen_address: str,
    verbose: bool,
    debug: bool,
):
    """
    Initializes the CLI context for the job scheduler application.
    
    Sets up logging, creates the job store, and prepares the task management system based on CLI options. Stores initialized components in the Click context for use by subcommands.
    """
    if verbose:
        setup_logging(debug=debug)
    store = JobStore \
        .from_address(address=store_address) \
        .with_options(schema=store_schema_name, table=store_table_name)  # fmt: skip
    supertask = Supertask(
        store=store,
        pre_delete_jobs=pre_delete_jobs,
    )
    ctx.meta["store"] = store
    ctx.meta["supertask"] = supertask


@cli.command()
@click.argument("taskfile", type=str)
@click.pass_context
def run(ctx: click.Context, taskfile: str):
    """
    Run task manager.
    """
    supertask: Supertask = ctx.meta["supertask"]
    timetable = Timetable.load(taskfile)
    supertask.with_namespace(timetable.namespace).configure()

    tl = TimetableLoader(scheduler=supertask.scheduler)
    tl.load(timetable)
    supertask.start()
    # .with_http_server(listen_http=ctx.parent.params["http_listen_address"]) \  # noqa: ERA001
    supertask.run_forever()


if __name__ == "__main__":
    cli()
