"""Romanian-style currency formatting and parsing."""


def format_ron(value):
    """Format a float as Romanian currency: 5.325,54 RON"""
    if value == 0:
        return "0,00 RON"
    negative = value < 0
    value = abs(value)
    integer_part = int(value)
    decimal_part = round((value - integer_part) * 100)
    if decimal_part >= 100:
        integer_part += 1
        decimal_part -= 100
    # Add thousands separator (.)
    int_str = f"{integer_part:,}".replace(",", ".")
    result = f"{int_str},{decimal_part:02d} RON"
    return f"-{result}" if negative else result


def parse_ron_input(val):
    """Parse user input that may use comma or dot as decimal separator.

    Accepts: 5325,54  |  5.325,54  |  5325.54  |  5,325.54
    Returns float or raises ValueError.
    """
    v = val.strip()
    if not v:
        return 0.0

    # Remove spaces
    v = v.replace(" ", "")
    # Remove RON suffix if user pasted it
    v = v.replace("RON", "").replace("ron", "").replace("Lei", "").replace("lei", "").strip()

    if not v:
        return 0.0

    # Detect format: if both . and , exist, the last one is the decimal separator
    has_dot = "." in v
    has_comma = "," in v

    if has_dot and has_comma:
        # Find which is last
        last_dot = v.rfind(".")
        last_comma = v.rfind(",")
        if last_comma > last_dot:
            # European: 5.325,54 -> remove dots, replace comma with dot
            v = v.replace(".", "").replace(",", ".")
        else:
            # US: 5,325.54 -> remove commas
            v = v.replace(",", "")
    elif has_comma and not has_dot:
        # Could be 5325,54 (European decimal) or 5,325 (US thousands)
        # If exactly 2 digits after comma, treat as decimal
        parts = v.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            v = v.replace(",", ".")
        else:
            # Multiple commas or >2 digits after: treat commas as thousands
            v = v.replace(",", "")
    # If only dots, it's standard float notation (or thousands with no decimal)

    result = float(v)
    if result < 0:
        raise ValueError("Negative values not allowed")
    return result
