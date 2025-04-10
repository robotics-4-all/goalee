import os

ZERO_LOGS = int(os.getenv('GOALDSL_ZERO_LOGS', 0))
LOG_LEVEL = os.getenv("GOALDSL_LOG_LEVEL", "INFO")
GOAL_TICK_FREQ_HZ = int(os.getenv("GOAL_TICK_FREQ_HZ", 10))
