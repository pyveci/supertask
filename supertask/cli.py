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
    "--pre-seed-jobs", envvar="ST_JOBS_PRESEED", type=str, required=False, help="Pre-seed job store before starting"
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
    pre_seed_jobs: str,
    http_listen_address: str,
    verbose: bool,
    debug: bool,
):
    """Initializes CLI logging, job store, and task scheduler configuration.
    
    Sets up logging based on the verbose and debug flags, creates a job store from the provided SQLAlchemy
    URL with optional schema and table parameters, and initializes a task scheduler (supertask) with
    options to pre-delete and pre-seed jobs. The job store and task scheduler are stored in the Click
    context metadata for later use by subcommands.
    """
    if verbose:
        setup_logging(debug=debug)
    store = JobStore \
        .from_address(address=store_address) \
        .with_options(schema=store_schema_name, table=store_table_name)  # fmt: skip
    supertask = Supertask(
        store=store,
        pre_delete_jobs=pre_delete_jobs,
        pre_seed_jobs=pre_seed_jobs,
    )
    """
    if pre_seed_jobs:
        js = TimetableLoader(scheduler=st.scheduler)
        js.load(Timetable.load(pre_seed_jobs))
    """
    ctx.meta["store"] = store
    ctx.meta["supertask"] = supertask


@cli.command()
@click.argument("taskfile", type=str)
@click.pass_context
def run(ctx: click.Context, taskfile: str):
    """
    Run the task manager indefinitely using tasks from a timetable file.
    
    This function retrieves a preconfigured task manager from the Click context,
    loads a timetable from the specified file, and configures the task manager using
    the timetable's namespace. A timetable loader is then used to incorporate the
    tasks into the scheduler. After starting the task manager, it enters an infinite
    loop to continuously execute the scheduled tasks.
    
    Parameters:
        taskfile (str): Path to the file defining the timetable for task scheduling.
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
