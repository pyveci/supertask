import click
from dotenv import load_dotenv, find_dotenv

from core import Supertask
from job_seeder import JobSeeder
from util import setup_logging


load_dotenv(find_dotenv())


@click.command()
@click.option("--store-address", envvar="ST_STORE_ADDRESS", type=str, required=True, help="SQLAlchemy URL of job store")
@click.option("--pre-delete-jobs", envvar="ST_JOBS_DELETE", is_flag=True, required=False, help="Prune job store before starting")
@click.option("--pre-seed-jobs", envvar="ST_JOBS_PRESEED", type=str, required=False, help="Pre-seed job store before starting")
@click.option("--http-listen-address", envvar="ST_HTTP_LISTEN_ADDRESS", type=str, required=False, help="HTTP API service listen address")
@click.option("--verbose", is_flag=True, required=False, default=True, help="Turn logging on/off")
@click.option("--debug", is_flag=True, required=False, help="Turn on logging with debug level")
@click.pass_context
def cli(ctx: click.Context, store_address: str, pre_delete_jobs: bool, pre_seed_jobs: str, http_listen_address: str, verbose: bool, debug: bool):
    if verbose:
        setup_logging(debug=debug)
    st = Supertask(job_store_address=store_address, pre_delete_jobs=pre_delete_jobs, pre_seed_jobs=pre_seed_jobs)
    if pre_seed_jobs:
        js = JobSeeder(source=pre_seed_jobs, scheduler=st.scheduler)
        js.seed_jobs()
    st.start(listen_http=http_listen_address)
    st.wait()


if __name__ == "__main__":
    cli()
