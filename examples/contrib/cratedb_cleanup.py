#!/usr/bin/env python3
# ruff: noqa: ERA001, T201

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

import logging
import os
import re
import sys
import time
import typing as t

import sqlalchemy as sa
from cratedb_toolkit.model import TableAddress

logger = logging.getLogger(__name__)


class DatabaseCleanupTask:
    """
    A task definition to clean up temporary tables in a database.
    """

    def __init__(self, schemas: t.Optional[t.List[str]] = None, table_prefixes: t.Optional[t.List[str]] = None):
        self.schemas = schemas
        self.table_prefixes = table_prefixes
        database_url = os.getenv("DATABASE_URL")
        if database_url is None:
            raise ValueError("Database URL environment variable is not set: DATABASE_URL")
        self.engine = sa.create_engine(database_url, echo=os.getenv("ST_SQL_ECHO", "").lower() in ("true", "1", "yes"))

    def run(self) -> None:
        """
        Inquire relevant table addresses and clean up temporary tables.
        """
        try:
            with self.engine.connect() as conn:
                for table in self.table_addresses:
                    # TODO: Can CrateDB use parameterized DDL identifiers?
                    sql = f"DROP TABLE IF EXISTS {table.fullname}"
                    logger.info(f"Dropping table {table.fullname}: {sql}")
                    conn.execute(sa.text(sql))
        except Exception:
            logger.exception("Database connection error")
            time.sleep(1)

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

        # Only check tables from schemas we're interested in.
        schemas_to_check = [schema for schema in inspector.get_schema_names() if schema in self.schemas]

        # Pre-compile a regex pattern for efficiency if many tables need to be checked.
        prefix_pattern = "^(" + "|".join(re.escape(prefix) for prefix in self.table_prefixes) + ")"
        pattern = re.compile(prefix_pattern)

        for schema in schemas_to_check:
            tables = inspector.get_table_names(schema=schema)
            for table in tables:
                if pattern.match(table):
                    bucket.append(TableAddress(schema=schema, table=table))
        return bucket


def run(**kwargs):
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
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
