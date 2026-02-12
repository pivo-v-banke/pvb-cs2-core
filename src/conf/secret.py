import os

from utils.type_cast import strtobool

CONNECTOR_API_SECRET_KEY = os.getenv("CONNECTOR_API_SECRET_KEY", "default")
CONNECTOR_API_SECRET_KEY_REQUIRED = strtobool(os.getenv("CONNECTOR_API_SECRET_KEY_REQUIRED", "true"))
