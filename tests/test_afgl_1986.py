"""Test cases for the afgl_1986 module."""
import pandas as pd
import pytest
import xarray as xr

from joseki import afgl_1986


@pytest.mark.parametrize("identifier", [n for n in afgl_1986.Identifier])
def test_parse_returns_dataframe(identifier: afgl_1986.Identifier) -> None:
    """Returns a pandas's DataFrame."""
    df = afgl_1986.parse(identifier=identifier)
    assert isinstance(df, pd.DataFrame)


@pytest.mark.parametrize("identifier", [n for n in afgl_1986.Identifier])
def test_parse_identifier(identifier: afgl_1986.Identifier) -> None:
    """Handles all supported identifier values."""
    afgl_1986.parse(identifier=identifier)


@pytest.mark.parametrize("identifier", [n for n in afgl_1986.Identifier])
def test_to_xarray_returns_dataset(identifier: afgl_1986.Identifier) -> None:
    """Returns a Dataset."""
    df = afgl_1986.parse(identifier=identifier)
    assert isinstance(afgl_1986.to_xarray(df=df, identifier=identifier), xr.Dataset)


@pytest.mark.parametrize("identifier", [n for n in afgl_1986.Identifier])
def test_to_xarray_all_coords(identifier: afgl_1986.Identifier) -> None:
    """Adds all expected coordinates to data set."""
    df = afgl_1986.parse(identifier=identifier)
    ds = afgl_1986.to_xarray(df=df, identifier=identifier)
    expected_coords = ["zn", "species"]
    assert all([coord in ds.coords for coord in expected_coords])


@pytest.mark.parametrize("identifier", [n for n in afgl_1986.Identifier])
def test_to_xarray_all_data_vars(identifier: afgl_1986.Identifier) -> None:
    """Adds all expected data variables to data set."""
    df = afgl_1986.parse(identifier=identifier)
    ds = afgl_1986.to_xarray(df=df, identifier=identifier)
    expected_data_vars = ["p", "t", "n", "mr"]
    assert all([data_var in ds.data_vars for data_var in expected_data_vars])


@pytest.mark.parametrize("identifier", [n for n in afgl_1986.Identifier])
def test_to_xarray_attrs(identifier: afgl_1986.Identifier) -> None:
    """Adds all expected attributes to data set."""
    df = afgl_1986.parse(identifier=identifier)
    ds = afgl_1986.to_xarray(df=df, identifier=identifier)
    expected_attrs = ["convention", "title", "source", "history", "references"]
    assert all([attr in ds.attrs for attr in expected_attrs])


@pytest.mark.parametrize("identifier", [n for n in afgl_1986.Identifier])
def test_read(identifier: afgl_1986.Identifier) -> None:
    """Is equivalent to calling parse and then to_xarray."""
    df = afgl_1986.parse(identifier=identifier)
    ds = afgl_1986.to_xarray(df=df, identifier=identifier)
    assert ds == afgl_1986.read(identifier=identifier)
