# -*- coding: utf-8 -*-

"""Project config.

"""

from os import path, sep, environ
from typing import Dict, Any


__all__ = [
    "BASE_DIR",
    "METER_CONFIG",
    "REDIS_CONFIG",
    "EMAIL_CONFIG",
    "NOTIFIER",
    "SUBSCRIBE",
    "ACCOUNT",
    "PERMISSION",
    "AWS_CONFIG",
    "QUERY_CONFIG",
    "DELETE_CONFIG",
    "SQLALCHEMY_CONFIG",
    "LOGGING_CONFIG",
]


ROOT = path.abspath(sep)

BASE_DIR = path.dirname(path.dirname(__file__))
"""Module root directory."""

REDIS_CONFIG = {
    "password": str(environ.get("REDIS_PASSWORD")),
    "host": str(environ.get("REDIS_HOST")),
    "port": str(environ.get("REDIS_PORT", "6379")),
    "db": str(environ.get("REDIS_DB")),
}
"""Redis config."""

_IN_PRODUCTION = int(environ.get("IN_PRODUCTION", "0")) == 1

_NAMESPACE_TO_WEB = {
    "backend": "web.dev.my_website.com",
    "test": "web.test.my_website.com",
    "system": "www.my_website.com" if _IN_PRODUCTION else "web.sys.my_website.com",
    "poc": "web.poc.my_website.com",
    "demo": "web.demo.my_website.com",
}

EMAIL_CONFIG = {
    "website": f'https://{_NAMESPACE_TO_WEB[environ.get("POD_NAMESPACE", "backend")]}/',
    "support_email": str(environ.get("SUPPORT_EMAIL")),
    "retention": str(environ.get("TAKEOUT_RETENTION_DAYS")),
    "admin_email": str(environ.get("ADMIN_EMAIL")),
}
"""email config."""

NOTIFIER = {
    "host": str(environ.get("NOTIFIER_HOST")),
    "port": str(environ.get("NOTIFIER_SERVICE_PORT_GRPC")),
}
"""notifier service config."""

SUBSCRIBE = {
    "host": str(environ.get("SUBSCRIBE_HOST")),
    "port": str(environ.get("SUBSCRIBE_SERVICE_PORT_GRPC")),
}
"""subscribe service config."""

ACCOUNT = {
    "host": str(environ.get("ACCOUNT_HOST")),
    "port": str(environ.get("ACCOUNT_SERVICE_PORT_GRPC")),
}
"""account service config."""

PERMISSION: Dict[str, Any] = {
    "host": str(environ.get("AUTHPOINT2_PERMISSION_HOST")),
    "port": str(environ.get("AUTHPOINT2_PERMISSION_SERVICE_PORT_GRPC")),
}
"""permission service config."""

AWS_CONFIG = {
    "region": str(environ.get("AWS_REGION")),
    "access_key_id": str(environ.get("AWS_ACCESS_KEY_ID")),
    "secret_key": str(environ.get("AWS_SECRET_KEY")),
    "takeout_bucket_name": str(environ.get("AWS_TAKEOUT_BUCKET")),
    "archive_bucket_name": str(environ.get("AWS_ARCHIVE_BUCKET")),
}
"""AWS resource config."""

QUERY_CONFIG = {
    "host": str(environ.get("PROMETHEUS_QUERY_HOST")),
    "host2": str(environ.get("PROMETHEUS_QUERY_HOST")),
    "port": str(environ.get("PROMETHEUS_QUERY_PORT", "9090")),
    "dir": "/tmp",
    "earliestYear": "2021",
}
"""Query config."""

if environ.get("POD_NAMESPACE") and environ.get("PROMETHEUS_LOKI_QUERY_OTHER_NAMESPACE"):
    ns = str(environ.get("POD_NAMESPACE"))
    key = f"PROMETHEUS_LOKI_QUERY_{ns.upper()}_HOST"
    if ns in str(environ.get("PROMETHEUS_LOKI_QUERY_OTHER_NAMESPACE")) and environ.get(key):
        QUERY_CONFIG["host2"] = str(environ.get(key))

DELETE_CONFIG = {
    "thanos": "/usr/svc/thanos",
    "objstore": "/usr/svc/objstore.yml",
    "label": str(environ.get("PROMETHEUS_INSTANCE")),
}
"""Delete config."""

SQLALCHEMY_CONFIG = {
    "dashboard_link": "postgresql+psycopg2://{user_name}:{password}@{host}/{dashboard_db}",
    "gateway_link": "postgresql+psycopg2://{user_name}:{password}@{host}/{gateway_db}",
    "user_name": str(environ.get("DB_USER")),
    "password": str(environ.get("DB_PASSWORD")),
    "host": str(environ.get("DB_HOST")),
    "dashboard_db": str(environ.get("DB_NAME_DASHBOARD")),
    "gateway_db": str(environ.get("DB_NAME_GATEWAY")),
}
"""SQLAlchemy config."""

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "formatters": {
        "console": {
            "()": "colorlog.ColoredFormatter",
            "format": "[%(log_color)s%(asctime)s %(levelname)-8s %(name)-8s %(module)-15s:%(lineno)6d] %(reset)s%(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "format": "[%(asctime)s %(levelname)-8s %(name)-8s %(module)-15s:%(lineno)6d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "colorlog.StreamHandler",
            "formatter": "console",
        },
        "logfile": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": path.join(ROOT, "var", "log", "myservice.log"),
            "when": "midnight",
            "backupCount": 30,
            "formatter": "file",
        },
    },
    "loggers": {
        "myservice": {
            "handlers": ["logfile", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
"""Log config."""
