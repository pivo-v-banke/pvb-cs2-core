import os

LOGGING_CONFIG = {
    "level": os.getenv("LOGGING_LEVEL", "INFO"),
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
        "": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        "app": {"handlers": ["default"], "level": "DEBUG", "propagate": False},
        "SteamClient": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["celery"], "level": os.getenv("CELERY_LOGGING_LEVEL", "INFO"), "propagate": False},
        "celery.app.trace": {"handlers": ["celery"], "level": os.getenv("CELERY_LOGGING_LEVEL", "INFO"), "propagate": False},
        "celery.worker": {"handlers": ["celery"], "level": os.getenv("CELERY_LOGGING_LEVEL", "INFO"), "propagate": False},
        "celery.redirected": {"handlers": ["celery"], "level": os.getenv("CELERY_LOGGING_LEVEL", "INFO"), "propagate": False},
        "kombu": {"handlers": ["celery"], "level": os.getenv("CELERY_LOGGING_LEVEL", "WARNING"), "propagate": False},
        "amqp": {"handlers": ["celery"], "level": os.getenv("CELERY_LOGGING_LEVEL", "WARNING"), "propagate": False},
        "billiard": {"handlers": ["celery"], "level": os.getenv("CELERY_LOGGING_LEVEL", "WARNING"), "propagate": False},
    },
}