# -*- coding: utf-8 -*-

"""Debug overriding config.

"""

from os import path
from .default import BASE_DIR


LOGGING_CONFIG = {
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "logfile": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": path.join(BASE_DIR, "..", "log", "myservice.log"),
            "when": "midnight",
            "backupCount": 30,
            "formatter": "file",
        },
    },
    "loggers": {
        "myservice": {
            "handlers": ["logfile", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
"""Log config."""
