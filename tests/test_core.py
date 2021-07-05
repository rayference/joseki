"""Test cases for the core module."""
import pathlib
from typing import Any

import numpy as np
import pytest
import xarray as xr

from joseki import afgl_1986
from joseki import core


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
    """'z' and 'z_bounds' are both coordinates but first is dim."""
    ds = afgl_1986.read(name="tropical")
    interpolated = core.represent_profile_in_cells(ds)
    for coord in ["z", "z_bounds"]:
        assert coord in interpolated.coords
    assert "z" in interpolated.dims and "z_bounds" not in interpolated.dims


def test_make() -> None:
    """Returns xr.Dataset."""
    assert isinstance(core.make(identifier="afgl_1986-tropical"), xr.Dataset)


def test_make_rfm_day() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-day"), xr.Dataset)


def test_make_rfm_equ() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-equ"), xr.Dataset)


def test_make_rfm_ngt() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-ngt"), xr.Dataset)


def test_make_rfm_sum() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-sum"), xr.Dataset)


def test_make_rfm_win() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-win"), xr.Dataset)


def test_make_rfm_mls() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-mls"), xr.Dataset)


def test_make_rfm_mlw() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-mlw"), xr.Dataset)


def test_make_rfm_saw() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-saw"), xr.Dataset)


def test_make_rfm_sas() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-sas"), xr.Dataset)


def test_make_rfm_std() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-std"), xr.Dataset)


def test_make_rfm_tro() -> None:
    """."""
    assert isinstance(core.make(identifier="rfm-tro"), xr.Dataset)


def test_make_invalid_identifier() -> None:
    """Raises if identifier is invalid."""
    with pytest.raises(ValueError):
        core.make(identifier="unknown-tropical"), xr.Dataset


def test_make_represent_in_cells() -> None:
    """Returned data set has z and zbv dimensions."""
    ds = core.make(
        identifier="afgl_1986-tropical",
        represent_in_cells=True,
    )
    for dim in ["z", "zbv"]:
        assert dim in ds.dims


def test_make_altitudes(tmpdir: Any) -> None:
    """Assigns data set' altitude values from file."""
    z_values = np.linspace(0, 120, 121)
    path = pathlib.Path(tmpdir, "z.txt")
    np.savetxt(path, z_values)
    ds = core.make(identifier="afgl_1986-tropical", altitudes=path)
    assert np.allclose(ds.z.values, z_values)
