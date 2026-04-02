import pytest
from backend.core.formatting import format_ron, parse_ron_input


# --- format_ron ---

def test_format_ron_simple():
    assert format_ron(234.54) == "234,54 RON"


def test_format_ron_thousands():
    assert format_ron(5325.54) == "5.325,54 RON"


def test_format_ron_large():
    assert format_ron(14639.64) == "14.639,64 RON"


def test_format_ron_zero():
    assert format_ron(0) == "0,00 RON"


def test_format_ron_whole_number():
    assert format_ron(1000.00) == "1.000,00 RON"


def test_format_ron_small():
    assert format_ron(3.50) == "3,50 RON"


# --- parse_ron_input ---

def test_parse_european_decimal():
    assert parse_ron_input("5325,54") == 5325.54


def test_parse_european_thousands():
    assert parse_ron_input("5.325,54") == 5325.54


def test_parse_us_decimal():
    assert parse_ron_input("5325.54") == 5325.54


def test_parse_us_thousands():
    assert parse_ron_input("5,325.54") == 5325.54


def test_parse_empty():
    assert parse_ron_input("") == 0.0
    assert parse_ron_input("   ") == 0.0


def test_parse_with_ron_suffix():
    assert parse_ron_input("5325,54 RON") == 5325.54


def test_parse_integer():
    assert parse_ron_input("1000") == 1000.0


def test_parse_negative_raises():
    with pytest.raises(ValueError):
        parse_ron_input("-500")


def test_parse_comma_only_two_decimals():
    """5325,54 should be treated as decimal, not thousands."""
    assert parse_ron_input("325,54") == 325.54


def test_parse_comma_thousands_no_decimal():
    """5,325 with 3 digits after comma = thousands separator."""
    assert parse_ron_input("5,325") == 5325.0
