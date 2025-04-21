import logging
import re
import typing as t

import colorlog
import tomli
from colorlog.escape_codes import escape_codes
from pueblo.sfa.pep723 import PEP_723_REGEX


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


def read_inline_script_metadata(type_: str, script: str) -> t.Dict[str, t.Any]:
    """
    Reference implementation to read inline script metadata (PEP 723).

    https://packaging.python.org/en/latest/specifications/inline-script-metadata/
    https://peps.python.org/pep-0723/

    TODO: Synchronize with `pueblo.sfa.pep723`.
    """

    name = type_ or "script"
    matches = list(filter(lambda m: m.group("type") == name, re.finditer(PEP_723_REGEX, script)))
    if len(matches) > 1:
        raise ValueError(f"Multiple {name} blocks found")
    if len(matches) == 1:
        content = "".join(
            line[2:] if line.startswith("# ") else line[1:]
            for line in matches[0].group("content").splitlines(keepends=True)
        )
        return tomli.loads(content)
    return {}
