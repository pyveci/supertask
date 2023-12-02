import dataclasses


@dataclasses.dataclass
class Settings:
    """
    Bundle settings for propagating them from the environment to the FastAPI domain.
    """
    store_address: str
    pre_delete_jobs: bool
    pre_seed_jobs: str
