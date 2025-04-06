import click
from dotenv import find_dotenv, load_dotenv

from supertask.core import Supertask
from supertask.model import JobStoreLocation
from supertask.provision.seeder import JobSeeder
from supertask.util import setup_logging

# TODO: Gate behind an environment variable?
load_dotenv(find_dotenv())


@click.command()
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
    if verbose:
        setup_logging(debug=debug)
    store_location = JobStoreLocation(address=store_address)
    if store_schema_name:
        store_location.schema = store_schema_name
    if store_table_name:
        store_location.table = store_table_name
    st = Supertask(store=store_location, pre_delete_jobs=pre_delete_jobs, pre_seed_jobs=pre_seed_jobs)
    if pre_seed_jobs:
        js = JobSeeder(source=pre_seed_jobs, scheduler=st.scheduler)
        js.seed_jobs()
    st.start(listen_http=http_listen_address)
    st.wait()


if __name__ == "__main__":
    cli()
