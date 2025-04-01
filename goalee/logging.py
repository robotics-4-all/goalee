import logging
import os
from rich.logging import RichHandler

ZERO_LOGS = int(os.getenv('GOALDSL_ZERO_LOGS', 0))
LOG_LEVEL = os.getenv("GOALDSL_LOG_LEVEL", "INFO")

if ZERO_LOGS:
    logging.disable()
else:
    LOGGING_FORMAT = "%(message)s"
    logging.basicConfig(
        format=LOGGING_FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    logging.getLogger().setLevel(LOG_LEVEL)

default_logger = logging.getLogger()
