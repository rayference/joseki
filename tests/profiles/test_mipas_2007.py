"""Test cases for the mipas_2007 module."""
import numpy as np
import pytest

from joseki.profiles.mipas_2007 import (
    Identifier,
    MIPASMidlatitudeDay,
    MIPASMidlatitudeNight,
    MIPASPolarSummer,
    MIPASPolarWinter,
    MIPASTropical,
    parse_content,
    parse_units,
    parse_values_line,
    parse_var_line,
    parse_var_name,
    read_file_content,
    to_chemical_formula,
    to_dataset,
    translate_cfc,
)
from joseki.units import ureg


def test_parse_unit():
    """Returns expected units."""
    assert parse_units("[K]") == "K"
    assert parse_units("[mb]") == "millibar"


def test_parse_unit_invalid():
    """Invalid unit string raises ValueError."""
    with pytest.raises(ValueError):
        parse_units("[missing right bracket")

    with pytest.raises(ValueError):
        parse_units("missing left bracket]")

    with pytest.raises(ValueError):
        parse_units("missing right and left bracket")


def test_parse_var_name():
    """Variable names are translated as expected."""
    assert parse_var_name("HGT") == "z"
    assert parse_var_name("PRE") == "p"
    assert parse_var_name("TEM") == "t"
    assert parse_var_name("other") == "other"


def test_parse_var_line_2_parts():
    """Parse 2-part line."""
    s = "*VAR_NAME [VAR_UNITS]"
    var_name, var_units = parse_var_line(s)
    assert var_name == "VAR_NAME" and var_units == "VAR_UNITS"


def test_parse_var_line_3_parts():
    """Parse 3-part line."""
    s = "*VAR_NAME (ALIAS) [VAR_UNITS]"
    var_name, var_units = parse_var_line(s)
    assert var_name == "VAR_NAME" and var_units == "VAR_UNITS"


def test_parse_var_line_invalid():
    """Raises ValueError when line has invalid format."""
    invalid_lines = ["*VAR_NAME", "*VAR_NAME (ALIAS) [VAR_UNITS] extra"]
    for invalid_line in invalid_lines:
        with pytest.raises(ValueError):
            parse_var_line(invalid_line)


def test_parse_values_line_whitespace():
    """Parse with whitespace delimiter."""
    s = "1.0 12.0  5.0       4.0 0.0"
    assert parse_values_line(s) == ["1.0", "12.0", "5.0", "4.0", "0.0"]


def test_parse_values_line_commas_and_whitespace():
    """Parse with commas and whitespace delimiters combined."""
    s = "1.0,2.0,   3.0    , 7.0      ,10.0"
    assert parse_values_line(s) == ["1.0", "2.0", "3.0", "7.0", "10.0"]


def test_parse_values_line_commas_and_whitespace_ends_with_comma():
    """Parse with commas and whitespace delimiters combined."""
    s = "1.0,2.0,   3.0    , 7.0      ,10.0 ,"
    assert parse_values_line(s) == ["1.0", "2.0", "3.0", "7.0", "10.0"]


def test_parse_content():
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

    output = parse_content(lines)
    assert isinstance(output, dict)
    assert "x_N2" in output
    assert "x_O2" in output


def test_parse_content_2():
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

    output = parse_content(lines)
    assert isinstance(output, dict)


def test_read_file_content():
    """Returns a tuple."""
    output = read_file_content(identifier=Identifier.MIDLATITUDE_DAY)
    assert isinstance(output, str)


def test_translate_cfc():
    """Converts F13 into CClF3."""
    assert translate_cfc("F13") == "CClF3"


def test_translate_cfc_unknown():
    """Raises when the chlorofulorocarbon is unknown."""
    with pytest.raises(ValueError):
        translate_cfc("unknown")


def test_to_chemical_formula_cfc():
    """Converts a chlorofulorocarbon name to its chemical formula."""
    assert to_chemical_formula("F13") == "CClF3"


def test_to_chemical_formula_h2o():
    """Returns non-chlorofulorocarbon name unchanged."""
    assert to_chemical_formula("H2O") == "H2O"


def test_to_dataset_z():
    ds = to_dataset(
        identifier=Identifier.TROPICAL,
        z=np.linspace(0, 10, 11) * ureg.km,
    )
    assert ds.joseki.is_valid


@pytest.mark.parametrize(
    "profile",
    [
        MIPASMidlatitudeNight(),
        MIPASMidlatitudeDay(),
        MIPASPolarSummer(),
        MIPASPolarWinter(),
        MIPASTropical(),
    ],
)
def test_profile_to_dataset(profile):
    """Returns a dataset."""
    ds = profile.to_dataset()
    assert ds.joseki.is_valid
