import base64

import sqlalchemy as sa
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


class LargeBinary(sa.String):
    """A type for large binary byte data.

    The :class:`.LargeBinary` type corresponds to a large and/or unlengthed
    binary type for the target platform, such as BLOB on MySQL and BYTEA for
    PostgreSQL.  It also handles the necessary conversions for the DBAPI.

    """

    __visit_name__ = "large_binary"

    def bind_processor(self, dialect):
        if dialect.dbapi is None:
            return None

        # TODO: DBAPIBinary = dialect.dbapi.Binary

        def process(value):
            if value is not None:
                # TODO: return DBAPIBinary(value)
                return base64.b64encode(value).decode()
            else:
                return None

        return process

    # Python 3 has native bytes() type
    # both sqlite3 and pg8000 seem to return it,
    # psycopg2 as of 2.5 returns 'memoryview'
    def result_processor(self, dialect, coltype):
        if dialect.returns_native_bytes:
            return None

        def process(value):
            if value is not None:
                return base64.b64decode(value)
            return value

        return process


class CrateDBSQLAlchemyJobStore(SQLAlchemyJobStore):
    def __init__(self, *args, **kwargs):
        self.patchme()
        super().__init__(*args, **kwargs)

        def receive_after_execute(
            conn: sa.engine.Connection, clauseelement, multiparams, params, execution_options, result
        ):
            """
            Run a `REFRESH TABLE ...` command after each DML operation (INSERT, UPDATE, DELETE).
            """
            if isinstance(clauseelement, (sa.sql.Insert, sa.sql.Update, sa.sql.Delete)):
                conn.execute(sa.text(f"REFRESH TABLE {clauseelement.table}"))

        sa.event.listen(self.engine, "after_execute", receive_after_execute)

    def patchme(self):
        """
        A few patches to make the CrateDB SQLAlchemy dialect work.

        """
        from sqlalchemy_cratedb import dialect
        from sqlalchemy_cratedb.compiler import CrateDDLCompiler, CrateTypeCompiler

        def visit_BLOB(self, type_, **kw):
            return "STRING"

        def visit_FLOAT(self, type_, **kw):
            """
            From `sqlalchemy.sql.sqltypes.Float`.

            When a :paramref:`.Float.precision` is not provided in a
            :class:`_types.Float` type some backend may compile this type as
            an 8 bytes / 64 bit float datatype. To use a 4 bytes / 32 bit float
            datatype a precision <= 24 can usually be provided or the
            :class:`_types.REAL` type can be used.
            This is known to be the case in the PostgreSQL and MSSQL dialects
            that render the type as ``FLOAT`` that's in both an alias of
            ``DOUBLE PRECISION``. Other third party dialects may have similar
            behavior.
            """
            if not type_.precision:
                return "FLOAT"
            elif type_.precision <= 24:
                return "FLOAT"
            else:
                return "DOUBLE"

        CrateTypeCompiler.visit_BLOB = visit_BLOB
        CrateTypeCompiler.visit_FLOAT = visit_FLOAT

        def visit_create_index(self, create, **kw):
            return "SELECT 1;"

        CrateDDLCompiler.visit_create_index = visit_create_index

        dialect.colspecs.update(
            {
                sa.sql.sqltypes.LargeBinary: LargeBinary,
            }
        )
