from decimal import Decimal


def format_number(value):
    """
    Format a number to remove trailing zeros.
    If it's a whole number, return an integer, otherwise return a float.
    """
    # Convert to Decimal for precise handling
    if isinstance(value, float) or isinstance(value, int) or isinstance(value, str):
        value = Decimal(str(value))

    # Check if it's a whole number
    if value % 1 == 0:
        return int(value)
    return float(
        str(value).rstrip("0").rstrip(".") if "." in str(value) else str(value)
    )
