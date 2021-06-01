"""Test cases for the core module."""
import pathlib
import tempfile

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from joseki import core


def test_read_raw_data_returns_dataframe() -> None:
    """Returns a pandas's DataFrame."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    assert isinstance(df, pd.DataFrame)


def test_read_raw_data_identifier() -> None:
    """Handles all supported identifier values."""
    for identifier in [
        "afgl_1986-tropical",
        "afgl_1986-midlatitude_summer",
        "afgl_1986-midlatitude_winter",
        "afgl_1986-subarctic_summer",
        "afgl_1986-subarctic_winter",
        "afgl_1986-us_standard",
    ]:
        core.read_raw_data(identifier=identifier)


def test_read_raw_data_invalid_identifier() -> None:
    """Raises when identifier is invalid."""
    with pytest.raises(ValueError):
        core.read_raw_data(identifier="invalid_identifier")


def test_to_xarray_returns_dataset() -> None:
    """Returns a xarray Dataset."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    assert isinstance(core.to_xarray(df), xr.Dataset)


def test_to_xarray_dataframes() -> None:
    """Handles all dataframes."""
    for identifier in [
        "afgl_1986-tropical",
        "afgl_1986-midlatitude_summer",
        "afgl_1986-midlatitude_winter",
        "afgl_1986-subarctic_summer",
        "afgl_1986-subarctic_winter",
        "afgl_1986-us_standard",
    ]:
        df = core.read_raw_data(identifier=identifier)
        core.to_xarray(df)


def test_to_xarray_all_coords() -> None:
    """Adds all expected coordinates to data set."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    ds = core.to_xarray(df)
    expected_coords = ["z_level", "species"]
    assert all([coord in ds.coords for coord in expected_coords])


def test_to_xarray_all_data_vars() -> None:
    """Adds all expected data variables to data set."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    ds = core.to_xarray(df)
    expected_data_vars = ["p", "t", "n", "mr"]
    assert all([data_var in ds.data_vars for data_var in expected_data_vars])


def test_to_xarray_attrs() -> None:
    """Adds all expected attributes to data set."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    ds = core.to_xarray(df)
    expected_attrs = ["convention", "title", "source", "history", "references"]
    assert all([attr in ds.attrs for attr in expected_attrs])


def test_read_raw_data_to_xarray() -> None:
    """Is equivalent to calling read_raw_data and then to_xarray."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    ds = core.to_xarray(df)
    assert ds == core.read_raw_data_to_xarray(identifier="afgl_1986-tropical")


def test_interp_returns_data_set() -> None:
    """Returns an xarray.Dataset."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    ds = core.to_xarray(df)
    interpolated = core.interp(ds=ds, z_level_new=np.linspace(0, 120, 121))
    assert isinstance(interpolated, xr.Dataset)


def test_interp_out_of_bound() -> None:
    """Raises when out of bounds values are provided."""
    with pytest.raises(ValueError):
        df = core.read_raw_data(identifier="afgl_1986-tropical")
        ds = core.to_xarray(df)
        core.interp(ds=ds, z_level_new=np.linspace(0, 150))


def test_set_main_coord_to_layer_altitude() -> None:
    """Returns a xarray.Dataset object."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    ds = core.to_xarray(df)
    interpolated = core.set_main_coord_to_layer_altitude(ds)
    assert isinstance(interpolated, xr.Dataset)


def test_set_main_coord_to_layer_altitude_coords() -> None:
    """'z_layer' is a dimension coord and 'z_level' is not."""
    df = core.read_raw_data(identifier="afgl_1986-tropical")
    ds = core.to_xarray(df)
    interpolated = core.set_main_coord_to_layer_altitude(ds)
    assert "z_layer" in interpolated.dims and "z_level" not in interpolated.dims


def test_make() -> None:
    """Returns xr.Dataset."""
    assert isinstance(core.make(identifier="afgl_1986-tropical"), xr.Dataset)


def test_make_set_main_coord() -> None:
    """Returned data set has a z_layer dimension."""
    ds = core.make(identifier="afgl_1986-tropical", main_coord_to_layer_altitude=True)
    assert "z_layer" in ds.dims


def test_make_level_altitudes() -> None:
    """Returned data set has a z_layer dimension."""
    z_level_values = np.linspace(0, 120, 121)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(tmpdir, "z_level.txt")
        np.savetxt(path, z_level_values)
        ds = core.make(identifier="afgl_1986-tropical", level_altitudes=path)
    assert np.allclose(ds.z_level.values, z_level_values)
