"""Test cases for the afgl_1986 module."""
import pandas as pd
import pytest
import xarray as xr

from joseki.afgl_1986 import Identifier
from joseki.afgl_1986 import parse
from joseki.afgl_1986 import read
from joseki.afgl_1986 import to_xarray


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_parse_returns_dataframe(identifier: Identifier) -> None:
    """Returns a pandas's DataFrame."""
    df = parse(identifier=identifier)
    assert isinstance(df, pd.DataFrame)


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_parse_identifier(identifier: Identifier) -> None:
    """Handles all supported identifier values."""
    parse(identifier=identifier)


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_to_xarray_returns_dataset(identifier: Identifier) -> None:
    """Returns a Dataset."""
    df = parse(identifier=identifier)
    assert isinstance(to_xarray(df=df, identifier=identifier), xr.Dataset)


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_to_xarray_all_coords(identifier: Identifier) -> None:
    """Adds all expected coordinates to data set."""
    df = parse(identifier=identifier)
    ds = to_xarray(df=df, identifier=identifier)
    expected_coords = ["zn", "species"]
    assert all([coord in ds.coords for coord in expected_coords])


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_to_xarray_all_data_vars(identifier: Identifier) -> None:
    """Adds all expected data variables to data set."""
    df = parse(identifier=identifier)
    ds = to_xarray(df=df, identifier=identifier)
    expected_data_vars = ["p", "t", "n", "x"]
    assert all([data_var in ds.data_vars for data_var in expected_data_vars])


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_to_xarray_attrs(identifier: Identifier) -> None:
    """Adds all expected attributes to data set."""
    df = parse(identifier=identifier)
    ds = to_xarray(df=df, identifier=identifier)
    expected_attrs = ["convention", "title", "source", "history", "references"]
    assert all([attr in ds.attrs for attr in expected_attrs])


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_read(identifier: Identifier) -> None:
    """Is equivalent to calling parse and then to_xarray."""
    df = parse(identifier=identifier)
    ds = to_xarray(df=df, identifier=identifier)
    assert ds == read(identifier=identifier)
