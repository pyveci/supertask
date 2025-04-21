#!/usr/bin/env python3
import logging
import os
import sys
import typing as t

# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "cratedb-toolkit",
#     "sqlalchemy-cratedb",
#     "tqdm",
# ]
# ///
##
# /// task
# cron = "*/5 * * * * * *"
# [env]
# DATABASE_URL = "crate://crate@localhost:4200/"
# [options]
# schemas = ["foo", "bar"]
# table_prefixes = ["tmp_", "temp_"]
# ///
import sqlalchemy as sa
from cratedb_toolkit.model import TableAddress

logger = logging.getLogger(__name__)


class DatabaseCleanupTask:
    """
    A task definition to clean up temporary tables in a database.
    """

    def __init__(self, schemas: t.List[str] = None, table_prefixes: t.List[str] = None):
        self.schemas = schemas
        self.table_prefixes = table_prefixes
        database_url = os.getenv("DATABASE_URL")
        if database_url is None:
            raise ValueError("Database URL environment variable is not set: DATABASE_URL")
        self.engine = sa.create_engine(database_url, echo=True)

    def run(self) -> None:
        """
        Inquire relevant table addresses and clean up temporary tables.
        """
        with self.engine.connect() as conn:
            for table in self.table_addresses:
                sql = f"DROP TABLE IF EXISTS {table.fullname}"
                logger.info(f"Dropping table {table.fullname}: {sql}")
                conn.execute(sa.text(sql))

    @property
    def table_addresses(self) -> t.List[TableAddress]:
        """
        Table addresses selected by filter.

        TODO: Elaborate with `include` vs. `exclude` selectors?
        TODO: Q: How to make the current prefix match (`table_prefixes`) more advanced?
              A: Just use regexes, or provide other wildcard schemes?
        TODO: Possibly refactor to stdlib or CrateDB Toolkit.
        """
        inspector = sa.inspect(self.engine)
        bucket: t.List[TableAddress] = []
        for schema in inspector.get_schema_names():
            if schema in self.schemas:
                tables = inspector.get_table_names(schema=schema)
                for table in tables:
                    for prefix in self.table_prefixes:
                        if table.startswith(prefix):
                            bucket.append(TableAddress(schema=schema, table=table))
        return bucket


def run(**kwargs):
    logging.basicConfig(level=logging.INFO, handlers=[sys.stderr])
    task = DatabaseCleanupTask(**kwargs)
    task.run()


if __name__ == "__main__":
    """
    crash -c "create table testdrive.tmp_foo (id int)"
    export DATABASE_URL=crate://crate@localhost:4200/
    python examples/contrib/cratedb_cleanup.py
    """
    run(
        schemas=["testdrive"],
        table_prefixes=["tmp_", "temp_"],
    )
