"""
class CrateDBMongoDBJobStore(MongoDBJobStore):
    from cratedb_toolkit.adapter.pymongo import PyMongoCrateDbAdapter
    def __init__(self, dburi, *args, **kwargs):
        with PyMongoCrateDbAdapter(dburi=dburi):
            super().__init__(*args, **kwargs)
"""


def CrateDBMongoDBJobStore(dburi: str):
    from cratedb_toolkit.adapter.pymongo import PyMongoCrateDbAdapter

    with PyMongoCrateDbAdapter(dburi=dburi):
        import pymongo

        amalgamated_client: pymongo.MongoClient = pymongo.MongoClient(
            "localhost", 27017, timeoutMS=100, connectTimeoutMS=100, socketTimeoutMS=100, serverSelectionTimeoutMS=100
        )
        from apscheduler.jobstores.mongodb import MongoDBJobStore

        class CrateDBMongoDBJobStoreImpl(MongoDBJobStore):
            def __init__(self, *args, **kwargs):
                kwargs["client"] = amalgamated_client
                super().__init__(*args, **kwargs)

        return CrateDBMongoDBJobStoreImpl()
