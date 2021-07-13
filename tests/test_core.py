"""Test cases for the core module."""
import pathlib
from typing import Any

import numpy as np
import pytest
import xarray as xr

from joseki import afgl_1986
from joseki import core
from joseki import rfm


IDENTIFIER_CHOICES = [f"rfm-{n.value}" for n in rfm.Name] + [
    f"afgl_1986-{n.value}" for n in afgl_1986.Name
]


def test_interp_returns_data_set() -> None:
    """Returns an xarray.Dataset."""
    ds = afgl_1986.read(name="tropical")
    interpolated = core.interp(ds=ds, z_new=np.linspace(0, 120, 121))
    assert isinstance(interpolated, xr.Dataset)


def test_interp_out_of_bound() -> None:
    """Raises when out of bounds values are provided."""
    with pytest.raises(ValueError):
        ds = afgl_1986.read(name="tropical")
        core.interp(ds=ds, z_new=np.linspace(0, 150))


def test_represent_profile_in_cells() -> None:
    """Returns a xarray.Dataset object."""
    ds = afgl_1986.read(name="tropical")
    interpolated = core.represent_profile_in_cells(ds)
    assert isinstance(interpolated, xr.Dataset)


def test_represent_profile_in_cells_coords() -> None:
    """'z' and 'zc' are both coordinates."""
    ds = afgl_1986.read(name="tropical")
    interpolated = core.represent_profile_in_cells(ds)
    for coord in ["zn", "zc"]:
        assert coord in interpolated.coords


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make(identifier: str) -> None:
    """Returns xr.Dataset."""
    assert isinstance(core.make(identifier=identifier), xr.Dataset)


def test_make_invalid_identifier() -> None:
    """Raises if identifier is invalid."""
    with pytest.raises(ValueError):
        core.make(identifier="unknown-tropical"), xr.Dataset


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make_represent_in_cells(identifier: str) -> None:
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
def test_make_altitudes(tmpdir: Any, identifier: str) -> None:
    """Assigns data set' altitude values from file."""
    z_values = np.linspace(0, 120, 121)
    path = pathlib.Path(tmpdir, "z.txt")
    np.savetxt(path, z_values)
    ds = core.make(identifier=identifier, altitudes=path)
    assert np.allclose(ds.zn.values, z_values)
