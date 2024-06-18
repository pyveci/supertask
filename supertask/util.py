import logging

import colorlog
from colorlog.escape_codes import escape_codes


def setup_logging(level=logging.INFO, debug: bool = False, width: int = 30):
    reset = escape_codes["reset"]
    log_format = f"%(asctime)-15s [%(name)-{width}s] %(log_color)s%(levelname)-8s:{reset} %(message)s"

    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(log_format))

    logging.basicConfig(format=log_format, level=level, handlers=[handler])

    # Enable SQLAlchemy logging.
    if debug:
        logging.getLogger("sqlalchemy").setLevel(level)

    logging.getLogger("crate.client").setLevel(level)
    logging.getLogger("sqlalchemy_cratedb").setLevel(level)
    logging.getLogger("urllib3.connectionpool").setLevel(level)
