import logging
import threading

import uvicorn
from fastapi import FastAPI

from supertask.http.routes import router as cronjob_router
from supertask.model import Settings

logger = logging.getLogger(__name__)


class HTTPAPI:
    def __init__(self, settings: Settings, listen_address: str, debug: bool = False):
        self.settings = settings
        self.listen_address = listen_address
        self.debug = debug

    def start(self):
        host, port_str = self.listen_address.split(":")
        port = int(port_str)

        logger.info(f"Starting HTTP service on: {host}:{port}")
        app = FastAPI(debug=self.debug)

        # Inject settings as dependency to FastAPI. Thanks, @Mause.
        # https://github.com/tiangolo/fastapi/issues/2372#issuecomment-732492116
        app.dependency_overrides[Settings] = lambda: self.settings

        app.include_router(cronjob_router)

        def run_server():
            uvicorn.run(app, host=host, port=port)

        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        return self
