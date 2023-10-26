"""Test cases for units module."""
import numpy as np
import pint
import pytest
import xarray as xr
from numpy.typing import ArrayLike

from joseki.units import ureg, to_quantity


@pytest.fixture
def dataset() -> xr.Dataset:
    """Fixture for working with a dummy dataset."""
    return xr.Dataset(
        data_vars={
            "x": ("t", np.random.random(50), {"units": "m"}),
            "y": ("t", np.random.random(50)),
        },
        coords={"t": ("t", np.linspace(0, 10, 50), {"units": "s"})},
    )

def test_to_quantity_invalid_type():
    """Raises a TypeError."""
    with pytest.raises(NotImplementedError):
        to_quantity("not a quantity")

def test_to_quantity_quantity():
    """Returns the same quantity."""
    q = ureg.Quantity(1.0, "m")
    assert to_quantity(q) is q

    assert to_quantity(q, units="cm").units == ureg.Unit("cm")

def test_to_quantity_dict():
    """Returns a quantity."""
    d = {"value": 1.0, "units": "m"}
    assert isinstance(to_quantity(d), pint.Quantity)

@pytest.mark.parametrize(
    "value",
    [
        1,
        1.0,
        [1.0, 2.0],
        [[1.0, 2.0], [3.0, 4.0]],
        np.array([1.0, 2.0])
    ],
)
def test_to_quantity_array_like(value: ArrayLike):
    """Returns a dimensionless quantity."""
    assert to_quantity(value).units == ureg.dimensionless
    assert to_quantity(value, units="m").units == ureg.Unit("m")

def test_to_quantity_da(dataset: xr.Dataset):
    """Returns a quantity."""
    assert isinstance(to_quantity(dataset.x), pint.Quantity)

def test_to_quantity_da_units(dataset: xr.Dataset):
    """Returns a quantity with cm units."""
    q = to_quantity(dataset.x, units="cm")
    assert q.units == ureg.Unit("cm")

def test_to_quantity_da_no_units_raise(dataset: xr.Dataset):
    """Returns a quantity."""
    with pytest.raises(ValueError):
        to_quantity(dataset.y)

def test_to_quantity_da_no_units_no_raise(dataset: xr.Dataset):
    """Returns a quantity."""
    assert isinstance(to_quantity(dataset.y, units="m"), pint.Quantity)
