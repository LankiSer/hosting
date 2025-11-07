"""
Конфигурация логирования для приложения
"""

import logging
import logging.config
from datetime import datetime
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

for subdir in ("app", "auth", "database", "errors", "integrations"):
    (LOG_DIR / subdir).mkdir(exist_ok=True)

current_date = datetime.now().strftime("%Y-%m-%d")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "{asctime} | {levelname:8} | {name:30} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{asctime} | {levelname:8} | {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": f"logs/app/app_{current_date}.log",
            "maxBytes": 10_485_760,
            "backupCount": 5,
            "encoding": "utf8",
        },
        "auth_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": f"logs/auth/auth_{current_date}.log",
            "maxBytes": 5_242_880,
            "backupCount": 5,
            "encoding": "utf8",
        },
        "database_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "formatter": "detailed",
            "filename": f"logs/database/database_{current_date}.log",
            "maxBytes": 5_242_880,
            "backupCount": 3,
            "encoding": "utf8",
        },
        "integrations_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": f"logs/integrations/ispmanager_{current_date}.log",
            "maxBytes": 5_242_880,
            "backupCount": 3,
            "encoding": "utf8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": f"logs/errors/errors_{current_date}.log",
            "maxBytes": 10_485_760,
            "backupCount": 10,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "app.main": {
            "level": "INFO",
            "handlers": ["console", "app_file"],
            "propagate": False,
        },
        "app.modules.auth": {
            "level": "INFO",
            "handlers": ["console", "auth_file"],
            "propagate": False,
        },
        "app.integrations.ispmanager": {
            "level": "INFO",
            "handlers": ["integrations_file"],
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "level": "WARNING",
            "handlers": ["database_file"],
            "propagate": False,
        },
        "sqlalchemy.pool": {
            "level": "WARNING",
            "handlers": ["database_file"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "ERROR",
            "handlers": ["error_file"],
            "propagate": False,
        },
        "fastapi": {
            "level": "WARNING",
            "handlers": ["error_file"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "app_file", "error_file"],
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)