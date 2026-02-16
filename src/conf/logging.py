import os

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
LOGGING_CONFIG = {
    "level": LOGGING_LEVEL,
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
        "access": {
            "format": "%(asctime)s | %(levelname)s | uvicorn.access | %(message)s",
        },
        "celery": {
            "format": "%(asctime)s | %(levelname)s | %(processName)s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "default": {"class": "logging.StreamHandler", "formatter": "default"},
        "access": {"class": "logging.StreamHandler", "formatter": "access"},
        "celery": {"class": "logging.StreamHandler", "formatter": "celery"},
    },
    "loggers": {
        "": {"handlers": ["default"], "level": LOGGING_LEVEL, "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": LOGGING_LEVEL, "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": LOGGING_LEVEL, "propagate": False},
        "app": {"handlers": ["default"], "level": LOGGING_LEVEL, "propagate": False},
        "SteamClient": {"handlers": ["default"], "level": LOGGING_LEVEL, "propagate": False},
        "celery": {"handlers": ["celery"], "level": LOGGING_LEVEL, "propagate": False},
        "celery.app.trace": {"handlers": ["celery"], "level": LOGGING_LEVEL, "propagate": False},
        "celery.worker": {"handlers": ["celery"], "level": "INFO", "propagate": False},
        "celery.redirected": {"handlers": ["celery"], "level": LOGGING_LEVEL, "propagate": False},
        "kombu": {"handlers": ["celery"], "level": LOGGING_LEVEL, "propagate": False},
        "amqp": {"handlers": ["celery"], "level": LOGGING_LEVEL, "propagate": False},
        "billiard": {"handlers": ["celery"], "level": LOGGING_LEVEL, "propagate": False},
    },
}