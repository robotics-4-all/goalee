import logging
from goalee import definitions as CONFIG

# Set up logging
logging.basicConfig(format="%(asctime)s - %(message)s")
if CONFIG.ZERO_LOGS: logging.disable()
else: logging.getLogger().setLevel(CONFIG.LOG_LEVEL)
# -------------------------------------------------------------

default_logger = logging.getLogger()
