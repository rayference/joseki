"""Test cases for the rfm module."""
from typing import Any

import pytest
import requests
import xarray as xr

from joseki import rfm


def test_parse_unit() -> None:
    """Returns expected units."""
    assert rfm._parse_units("[K]") == "K"
    assert rfm._parse_units("[mb]") == "millibar"


def test_parse_unit_invalid() -> None:
    """Invalid unit string raises ValueError."""
    with pytest.raises(ValueError):
        rfm._parse_units("[missing right bracket")

    with pytest.raises(ValueError):
        rfm._parse_units("missing left bracket]")

    with pytest.raises(ValueError):
        rfm._parse_units("missing right and left bracket")


def test_parse_var_name() -> None:
    """Variable names are translated as expected."""
    assert rfm._parse_var_name("HGT") == "z_level"
    assert rfm._parse_var_name("PRE") == "p"
    assert rfm._parse_var_name("TEM") == "t"
    assert rfm._parse_var_name("other") == "other"


def test_parse_var_line_2_parts() -> None:
    """Parse 2-part line."""
    s = "*VAR_NAME [VAR_UNITS]"
    var_name, var_units = rfm._parse_var_line(s)
    assert var_name == "VAR_NAME" and var_units == "VAR_UNITS"


def test_parse_var_line_3_parts() -> None:
    """Parse 3-part line."""
    s = "*VAR_NAME (ALIAS) [VAR_UNITS]"
    var_name, var_units = rfm._parse_var_line(s)
    assert var_name == "VAR_NAME" and var_units == "VAR_UNITS"


def test_parse_var_line_invalid() -> None:
    """Raises ValueError when line has invalid format."""
    invalid_lines = ["*VAR_NAME", "*VAR_NAME (ALIAS) [VAR_UNITS] extra"]
    for invalid_line in invalid_lines:
        with pytest.raises(ValueError):
            rfm._parse_var_line(invalid_line)


def test_parse_values_line_whitespace() -> None:
    """Parse with whitespace delimiter."""
    s = "1.0 12.0  5.0       4.0 0.0"
    assert rfm._parse_values_line(s) == ["1.0", "12.0", "5.0", "4.0", "0.0"]


def test_parse_values_line_commas_and_whitespace() -> None:
    """Parse with commas and whitespace delimiters combined."""
    s = "1.0,2.0,   3.0    , 7.0      ,10.0"
    assert rfm._parse_values_line(s) == ["1.0", "2.0", "3.0", "7.0", "10.0"]


def test_parse_values_line_commas_and_whitespace_ends_with_comma() -> None:
    """Parse with commas and whitespace delimiters combined."""
    s = "1.0,2.0,   3.0    , 7.0      ,10.0 ,"
    assert rfm._parse_values_line(s) == ["1.0", "2.0", "3.0", "7.0", "10.0"]


def test_parse_content() -> None:
    """Returns a dict."""
    lines = [
        "! Comment",
        "         11 ! Profile Levels",
        "*HGT [km]",
        "   0.0000000   1.0000000   2.0000000   3.0000000   4.0000000",
        "   5.0000000   6.0000000   7.0000000   8.0000000   9.0000000",
        "  10.0000000",
        "*PRE [mb]",
        " 1.01700E+03 9.01083E+02 7.96450E+02 7.02227E+02 6.17614E+02",
        " 5.41644E+02 4.73437E+02 4.12288E+02 3.57603E+02 3.08960E+02",
        " 2.65994E+02",
        "*TEM [K]",
        " 285.14 279.34 273.91 268.30 263.24",
        " 256.55 250.20 242.82 236.17 229.87",
        " 225.04",
        "*N2 [ppmv]",
        " 7.890e+05 7.890e+05 7.890e+05 7.890e+05 7.890e+05",
        " 7.890e+05 7.890e+05 7.890e+05 7.890e+05 7.890e+05",
        " 7.890e+05",
        "*O2 [ppmv]",
        " 2.120e+05 2.120e+05 2.120e+05 2.120e+05 2.120e+05",
        " 2.120e+05 2.120e+05 2.120e+05 2.120e+05 2.120e+05",
        " 2.120e+05",
        "*END",
    ]

    output = rfm._parse_content(lines)
    assert isinstance(output, dict)
    assert "N2" in output
    assert "O2" in output


def test_parse_content_2() -> None:
    """Returns a dict."""
    lines = [
        "! Comments",
        "         10 ! Profile Levels",
        "*HGT [km]",
        "   0.0000000   1.0000000   2.0000000   3.0000000   4.0000000",
        "   5.0000000   6.0000000   7.0000000   8.0000000   9.0000000",
        "*TEM [K]",
        " 285.14 279.34 273.91 268.30 263.24",
        " 256.55 250.20 242.82 236.17 229.87",
        "*N2 [ppmv]",
        " 7.890e+05 7.890e+05 7.890e+05 7.890e+05 7.890e+05",
        " 7.890e+05 7.890e+05 7.890e+05 7.890e+05 7.890e+05",
        "*O2 [ppmv]",
        " 2.120e+05 2.120e+05 2.120e+05 2.120e+05 2.120e+05",
        " 2.120e+05 2.120e+05 2.120e+05 2.120e+05 2.120e+05",
        "*PRE [mb]",
        " 1.01700E+03 9.01083E+02 7.96450E+02 7.02227E+02 6.17614E+02",
        " 5.41644E+02 4.73437E+02 4.12288E+02 3.57603E+02 3.08960E+02",
        "*END",
    ]

    output = rfm._parse_content(lines)
    assert isinstance(output, dict)


def test_read_file_content_day() -> None:
    """Returns a tuple."""
    output = rfm.read_file_content(name="day")
    assert isinstance(output, tuple)


def test_read_additional_species_day() -> None:
    """Returns a tuple."""
    output = rfm.read_additional_species(name="day")
    assert isinstance(output, tuple)


def test_read_additional_species_day_imk() -> None:
    """Returns a tuple."""
    output = rfm.read_additional_species(name="day_imk")
    assert isinstance(output, tuple)


def test_read_additional_species_std() -> None:
    """Returns a tuple."""
    output = rfm.read_additional_species(name="std")
    assert isinstance(output, tuple)


def test_read_additional_species_invalid() -> None:
    """Invalid name raises ValueError."""
    with pytest.raises(ValueError):
        rfm.read_additional_species(name="invalid")


def test_read() -> None:
    """Returns a :class:`~xarray.Dataset`."""
    ds = rfm.read(name="day")
    assert isinstance(ds, xr.Dataset)


def test_read_additional_species_true() -> None:
    """Returns a :class:`~xarray.Dataset`."""
    ds = rfm.read(name="day", additional_species=True)
    assert isinstance(ds, xr.Dataset)


def test_read_name() -> None:
    """Returns a :class:`~xarray.Dataset` for all identifier values."""
    for name in ["day", "equ", "ngt", "sum", "win"]:
        ds = rfm.read(name=name)
        assert isinstance(ds, xr.Dataset)


class MockConnectionError:
    """ConnectionError mock."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise requests.exceptions.ConnectionError


def test_read_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reads archived raw data files if connection error occurs."""
    monkeypatch.setattr("requests.get", MockConnectionError)
    ds = rfm.read(name="day")
    assert isinstance(ds, xr.Dataset)