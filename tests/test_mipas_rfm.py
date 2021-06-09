"""Test cases for the mipas_rfm module."""
import pytest
import xarray as xr

from joseki import mipas_rfm


def test_parse_unit() -> None:
    """Returns expected units."""
    assert mipas_rfm._parse_units("[K]") == "K"
    assert mipas_rfm._parse_units("[mb]") == "millibar"


def test_parse_unit_invalid() -> None:
    """Invalid unit string raises ValueError."""
    with pytest.raises(ValueError):
        mipas_rfm._parse_units("[missing right bracket")

    with pytest.raises(ValueError):
        mipas_rfm._parse_units("missing left bracket]")

    with pytest.raises(ValueError):
        mipas_rfm._parse_units("missing right and left bracket")


def test_parse_var_name() -> None:
    """Variable names are translated as expected."""
    assert mipas_rfm._parse_var_name("HGT") == "z_level"
    assert mipas_rfm._parse_var_name("PRE") == "p"
    assert mipas_rfm._parse_var_name("TEM") == "t"
    assert mipas_rfm._parse_var_name("other") == "other"


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

    output = mipas_rfm._parse_content(lines)
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

    output = mipas_rfm._parse_content(lines)
    assert isinstance(output, dict)


def test_read_mipas_data() -> None:
    """Returns a :class:`~xarray.Dataset`."""
    ds = mipas_rfm.read_raw_mipas_data(identifier="day")
    assert isinstance(ds, xr.Dataset)
