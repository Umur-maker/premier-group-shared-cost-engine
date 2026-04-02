"""Sanitize strings for use in filenames."""

import re

MAX_NAME_LEN = 50


def safe_name(name: str) -> str:
    """Strip filesystem-unsafe characters and cap length for filenames."""
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    s = s.replace("..", "").strip(". ")
    s = re.sub(r'\s+', '_', s)
    return s[:MAX_NAME_LEN]
