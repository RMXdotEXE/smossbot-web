


def trimStr(string, limit) -> str:
    """
    Converts input to a string, and trims it to the specified length.
    Returns the new string.
    """
    return string[:limit] if len(string) > limit else string


def strToBool(string) -> bool:
    """
    Converts a string to a boolean.
    Returns the result.
    """
    return str(string).lower() == "true"


def clampInt(_int, _min, _max) -> int:
    """
    Takes an integer and ensures it's clamped between the min and max.
    Returns the clamped integer.
    """
    if int(_int) < _min: return _min
    if int(_int) > _max: return _max
    return int(_int)


def cleanHexColorString() -> str:
    return ""