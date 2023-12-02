from core import Supertask
from job_seeder import JobSeeder
from util import setup_logging


if __name__ == "__main__":
    setup_logging()
    # TODO: Use only in sandbox mode, to have a fresh database canvas.
    pre_delete_jobs = True
    seed_jobs = True
    #run_supertask(job_store_address="memory://", pre_delete_jobs=pre_delete_jobs, seed_jobs=True)
    #run_supertask(job_store_address="postgresql://postgres@localhost", pre_delete_jobs=pre_delete_jobs, seed_jobs=True)
    st = Supertask(job_store_address="crate://localhost", pre_delete_jobs=pre_delete_jobs)
    if seed_jobs:
        js = JobSeeder(scheduler=st.scheduler)
        js.seed_jobs()
    st.start(listen_http="localhost:4243")
    st.wait()
