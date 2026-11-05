import logging
from pathlib import Path
import sys


def configure_logging(log_file: Path | None = None):
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file is not None:
        log_file.parent.mkdir(parents = True, exist_ok = True)
        handlers.append(logging.FileHandler(log_file, mode = "a", encoding = "utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
        force=True,
    )
