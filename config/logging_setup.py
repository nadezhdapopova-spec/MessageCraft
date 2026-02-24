import logging.config
from pathlib import Path

from django.apps import apps
from django.conf import settings


def setup_app_loggers():
    LOG_DIR = Path(settings.BASE_DIR) / "logs"
    LOG_DIR.mkdir(exist_ok=True)

    for app_config in apps.get_app_configs():
        app_label = app_config.label
        log_file = LOG_DIR / f"{app_label}.log"

        settings.LOGGING["handlers"][f"file_{app_label}"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        }

        settings.LOGGING["loggers"][app_label] = {
            "handlers": ["console", f"file_{app_label}"],
            "level": "INFO",
            "propagate": False,
        }

    logging.config.dictConfig(settings.LOGGING)
