from __future__ import annotations

import importlib
import logging
import os
from unittest.mock import patch


def test_default_logger_is_logger():
    from goalee.logging import default_logger

    assert isinstance(default_logger, logging.Logger)


def test_default_logger_is_root():
    from goalee.logging import default_logger

    assert default_logger.name == "root"


def test_logging_module_imports():
    from goalee import logging as goalee_logging

    assert hasattr(goalee_logging, "default_logger")


def test_zero_logs_disables_logging():
    with patch.dict(os.environ, {"GOALDSL_ZERO_LOGS": "1"}):
        import goalee.definitions as defs

        orig_zero = defs.ZERO_LOGS
        defs.ZERO_LOGS = 1
        try:
            import goalee.logging as gl

            importlib.reload(gl)
            assert hasattr(gl, "default_logger")
        finally:
            defs.ZERO_LOGS = orig_zero
            importlib.reload(gl)
