import dataclasses

from models import JobStoreLocation


@dataclasses.dataclass
class Settings:
    """
    Bundle settings for propagating them from the environment to the FastAPI domain.
    """
    store_location: JobStoreLocation
    pre_delete_jobs: bool
    pre_seed_jobs: str
