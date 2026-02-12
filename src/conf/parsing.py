import os

PARSING_DEDUP_KEY_TTL = int(os.getenv("PARSING_DEDUP_KEY_TTL", "3600"))
