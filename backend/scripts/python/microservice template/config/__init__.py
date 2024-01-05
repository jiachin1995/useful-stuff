# -*- coding: utf-8 -*-

import os
import json
import logging
import logging.config
from pathlib import Path

from .default import *


DEBUG = os.environ.get("DEBUG", "0") == "1"
"""Debug mode switch."""

if DEBUG:
    try:
        from . import debug_override

        override_items = [
            "LOGGING_CONFIG",
            "EMAIL_CONFIG",
            "NOTIFIER",
            "AWS_CONFIG",
            "QUERY_CONFIG",
            "DELETE_CONFIG",
            "SQLALCHEMY_CONFIG",
        ]
        lcl = locals()
        for item in override_items:
            if hasattr(debug_override, item):
                lcl[item].update(getattr(debug_override, item))
    except ImportError:
        print("No debug override")

# create log file
__filename = LOGGING_CONFIG["handlers"]["logfile"]["filename"]
Path(os.path.dirname(__filename)).mkdir(parents=True, exist_ok=True)
if not os.path.exists(__filename):
    open(__filename, "w+").close()

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("myservice")
""" Logger instance."""
logger.debug(f"DEBUG = {DEBUG}")
