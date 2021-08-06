"""Test cases for the utility module."""
import numpy as np
import pint
import pytest
import xarray as xr

from joseki.util import to_chemical_formula
from joseki.util import to_quantity
from joseki.util import translate_cfc


@pytest.fixture
def dataset() -> xr.Dataset:
    """Fixture for working with a dummy data set."""
    return xr.Dataset(
        data_vars={
            "x": ("t", np.random.random(50), {"units": "m"}),
            "y": ("t", np.random.random(50)),
        },
        coords={"t": ("t", np.linspace(0, 10, 50), {"units": "s"})},
    )


def test_to_quantity(dataset: xr.Dataset) -> None:
    """Returns a quantity."""
    assert isinstance(to_quantity(dataset.x), pint.Quantity)


def test_to_quantity_raises(dataset: xr.Dataset) -> None:
    """Raises when the DataArray's metadata does not contain a units field."""
    with pytest.raises(ValueError):
        to_quantity(dataset.y)


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
