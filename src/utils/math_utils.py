def clamp[T](
        x: T | None,
        min_value: T | None = None,
        max_value: T | None = None,
) -> T | None:

    if x is None:
        return None

    if min_value is not None and x < min_value:
        return min_value

    if max_value is not None and x > max_value:
        return max_value

    return x