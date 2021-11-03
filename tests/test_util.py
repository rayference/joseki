"""Test cases for the utility module."""
import pytest

from joseki.util import to_chemical_formula
from joseki.util import translate_cfc


def test_translate_cfc() -> None:
    """Converts F13 into CClF3."""
    assert translate_cfc("F13") == "CClF3"


def test_translate_cfc_unknown() -> None:
    """Raises when the chlorofulorocarbon is unknown."""
    with pytest.raises(ValueError):
        translate_cfc("unknown")


def test_to_chemical_formula_cfc() -> None:
    """Converts a chlorofulorocarbon name to its chemical formula."""
    assert to_chemical_formula("F13") == "CClF3"


def test_to_chemical_formula_h2o() -> None:
    """Returns non-chlorofulorocarbon name unchanged."""
    assert to_chemical_formula("H2O") == "H2O"
