"""Test cases for the core module."""
import pathlib
from typing import Any

import numpy as np
import pytest
import xarray as xr

from joseki import afgl_1986
from joseki import core


IDENTIFIER_CHOICES = [i for i in core.Identifier]


@pytest.fixture
def test_data_set() -> xr.Dataset:
    """Test data set fixture."""
    return afgl_1986.read(identifier=afgl_1986.Identifier.TROPICAL)


def test_interp_returns_data_set(test_data_set: xr.Dataset) -> None:
    """Returns an xarray.Dataset."""
    interpolated = core.interp(ds=test_data_set, z_new=np.linspace(0, 120, 121))
    assert isinstance(interpolated, xr.Dataset)


def test_interp_out_of_bound(test_data_set: xr.Dataset) -> None:
    """Raises when out of bounds values are provided."""
    with pytest.raises(ValueError):
        core.interp(ds=test_data_set, z_new=np.linspace(0, 150))


def test_represent_profile_in_cells(test_data_set: xr.Dataset) -> None:
    """Returns a xarray.Dataset object."""
    interpolated = core.represent_profile_in_cells(ds=test_data_set)
    assert isinstance(interpolated, xr.Dataset)


def test_represent_profile_in_cells_coords(test_data_set: xr.Dataset) -> None:
    """'z' and 'zc' are both coordinates."""
    interpolated = core.represent_profile_in_cells(ds=test_data_set)
    for coord in ["zn", "zc"]:
        assert coord in interpolated.coords


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make(identifier: core.Identifier) -> None:
    """Returns xr.Dataset."""
    assert isinstance(core.make(identifier=identifier), xr.Dataset)


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make_represent_in_cells(identifier: core.Identifier) -> None:
    """Returned data set has z and zc dimensions."""
    ds = core.make(
        identifier=identifier,
        represent_in_cells=True,
    )
    for dim in ["zn", "zc"]:
        assert dim in ds.dims


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make_altitudes(tmpdir: Any, identifier: core.Identifier) -> None:
    """Assigns data set' altitude values from file."""
    z_values = np.linspace(0, 120, 121)
    path = pathlib.Path(tmpdir, "z.txt")
    np.savetxt(path, z_values)
    ds = core.make(identifier=identifier, altitudes=path)
    assert np.allclose(ds.zn.values, z_values)
