"""Test cases for the core module."""
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
