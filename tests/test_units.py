"""Test cases for units module."""
import numpy as np
import pint
import pytest
import xarray as xr

from joseki.units import to_quantity


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


def test_to_quantity(dataset: xr.Dataset) -> None:
    """Returns a quantity."""
    assert isinstance(to_quantity(dataset.x), pint.Quantity)


def test_to_quantity_raises(dataset: xr.Dataset) -> None:
    """Raises when the DataArray's metadata does not contain a units field."""
    with pytest.raises(ValueError):
        to_quantity(dataset.y)
