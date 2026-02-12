def strtobool(value: str | None) -> bool:
    yes_values = {"yes", "on", "true", "t", "1"}

    return str(value).lower().strip() in yes_values
