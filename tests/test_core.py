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
    interpolated = core.interp(ds=ds, z_level_new=np.linspace(0, 120, 121))
    assert isinstance(interpolated, xr.Dataset)


def test_interp_out_of_bound() -> None:
    """Raises when out of bounds values are provided."""
    with pytest.raises(ValueError):
        ds = afgl_1986.read(name="tropical")
        core.interp(ds=ds, z_level_new=np.linspace(0, 150))


def test_set_main_coord_to_layer_altitude() -> None:
    """Returns a xarray.Dataset object."""
    ds = afgl_1986.read(name="tropical")
    interpolated = core.set_main_coord_to_layer_altitude(ds)
    assert isinstance(interpolated, xr.Dataset)


def test_set_main_coord_to_layer_altitude_coords() -> None:
    """'z_layer' and 'z_layer_bounds' are both coordinates but first is dim."""
    ds = afgl_1986.read(name="tropical")
    interpolated = core.set_main_coord_to_layer_altitude(ds)
    for coord in ["z_layer", "z_layer_bounds"]:
        assert coord in interpolated.coords
    assert "z_layer" in interpolated.dims and "z_layer_bounds" not in interpolated.dims


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


def test_make_set_main_coord() -> None:
    """Returned data set has a z_layer dimension."""
    ds = core.make(
        identifier="afgl_1986-tropical",
        main_coord_to_layer_altitude=True,
    )
    assert "z_layer" in ds.dims


def test_make_level_altitudes(tmpdir: Any) -> None:
    """Returned data set has a z_layer dimension."""
    z_level_values = np.linspace(0, 120, 121)
    path = pathlib.Path(tmpdir, "z_level.txt")
    np.savetxt(path, z_level_values)
    ds = core.make(identifier="afgl_1986-tropical", level_altitudes=path)
    assert np.allclose(ds.z_level.values, z_level_values)
