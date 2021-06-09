"""Test cases for the utility module."""
import numpy as np
import pint
import pytest
import xarray as xr

from joseki import util


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


def test_add_comment(dataset: xr.Dataset) -> None:
    """Adds comment to a data set."""
    util.add_comment(ds=dataset, comment="hello")
    assert dataset.attrs["comment"] == "hello"


def test_add_comment_append(dataset: xr.Dataset) -> None:
    """Appends comment to pre-existing comments."""
    dataset.attrs["comment"] = "hello"
    util.add_comment(ds=dataset, comment="world")
    assert dataset.attrs["comment"] == "hello\nworld"


def test_to_quantity(dataset: xr.Dataset) -> None:
    """Returns a quantity."""
    assert isinstance(util.to_quantity(dataset.x), pint.Quantity)


def test_to_quantity_raises(dataset: xr.Dataset) -> None:
    """Raises when the DataArray's metadata does not contain a units field."""
    with pytest.raises(ValueError):
        util.to_quantity(dataset.y)


def test_translate_cfc() -> None:
    """Converts F13 into CClF3."""
    assert util.translate_cfc("F13") == "CClF3"


def test_translate_cfc_unknown() -> None:
    """Raises when CFC name is unknown."""
    with pytest.raises(ValueError):
        util.translate_cfc("unknown_cfc")
