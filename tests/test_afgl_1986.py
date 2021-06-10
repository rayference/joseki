"""Test cases for the afgl_1986 module."""
import pandas as pd
import pytest
import xarray as xr

from joseki import afgl_1986


def test_parse_returns_dataframe() -> None:
    """Returns a pandas's DataFrame."""
    df = afgl_1986.parse(identifier="afgl_1986-tropical")
    assert isinstance(df, pd.DataFrame)


def test_parse_identifier() -> None:
    """Handles all supported identifier values."""
    for identifier in [
        "afgl_1986-tropical",
        "afgl_1986-midlatitude_summer",
        "afgl_1986-midlatitude_winter",
        "afgl_1986-subarctic_summer",
        "afgl_1986-subarctic_winter",
        "afgl_1986-us_standard",
    ]:
        afgl_1986.parse(identifier=identifier)


def test_parse_invalid_identifier() -> None:
    """Raises when identifier is invalid."""
    with pytest.raises(ValueError):
        afgl_1986.parse(identifier="invalid_identifier")


def test_to_xarray_returns_dataset() -> None:
    """Returns a xarray Dataset."""
    df = afgl_1986.parse(identifier="afgl_1986-tropical")
    assert isinstance(afgl_1986.to_xarray(df), xr.Dataset)


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
        df = afgl_1986.parse(identifier=identifier)
        afgl_1986.to_xarray(df)


def test_to_xarray_all_coords() -> None:
    """Adds all expected coordinates to data set."""
    df = afgl_1986.parse(identifier="afgl_1986-tropical")
    ds = afgl_1986.to_xarray(df)
    expected_coords = ["z_level", "species"]
    assert all([coord in ds.coords for coord in expected_coords])


def test_to_xarray_all_data_vars() -> None:
    """Adds all expected data variables to data set."""
    df = afgl_1986.parse(identifier="afgl_1986-tropical")
    ds = afgl_1986.to_xarray(df)
    expected_data_vars = ["p", "t", "n", "mr"]
    assert all([data_var in ds.data_vars for data_var in expected_data_vars])


def test_to_xarray_attrs() -> None:
    """Adds all expected attributes to data set."""
    df = afgl_1986.parse(identifier="afgl_1986-tropical")
    ds = afgl_1986.to_xarray(df)
    expected_attrs = ["convention", "title", "source", "history", "references"]
    assert all([attr in ds.attrs for attr in expected_attrs])


def test_read() -> None:
    """Is equivalent to calling parse and then to_xarray."""
    df = afgl_1986.parse(identifier="afgl_1986-tropical")
    ds = afgl_1986.to_xarray(df)
    assert ds == afgl_1986.read(identifier="afgl_1986-tropical")
