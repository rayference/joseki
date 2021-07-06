"""Test cases for the afgl_1986 module."""
import pandas as pd
import pytest
import xarray as xr

from joseki import afgl_1986


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_parse_returns_dataframe(name: afgl_1986.Name) -> None:
    """Returns a pandas's DataFrame."""
    df = afgl_1986.parse(name=name)
    assert isinstance(df, pd.DataFrame)


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_parse_identifier(name: afgl_1986.Name) -> None:
    """Handles all supported identifier values."""
    afgl_1986.parse(name=name)


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_to_xarray_returns_dataset(name: afgl_1986.Name) -> None:
    """Returns a Dataset."""
    df = afgl_1986.parse(name=name)
    assert isinstance(afgl_1986.to_xarray(df=df, name=name.value), xr.Dataset)


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_to_xarray_all_coords(name: afgl_1986.Name) -> None:
    """Adds all expected coordinates to data set."""
    df = afgl_1986.parse(name=name)
    ds = afgl_1986.to_xarray(df=df, name=name.value)
    expected_coords = ["z", "species"]
    assert all([coord in ds.coords for coord in expected_coords])


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_to_xarray_all_data_vars(name: afgl_1986.Name) -> None:
    """Adds all expected data variables to data set."""
    df = afgl_1986.parse(name=name)
    ds = afgl_1986.to_xarray(df=df, name=name.value)
    expected_data_vars = ["p", "t", "n", "mr"]
    assert all([data_var in ds.data_vars for data_var in expected_data_vars])


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_to_xarray_attrs(name: afgl_1986.Name) -> None:
    """Adds all expected attributes to data set."""
    df = afgl_1986.parse(name=name)
    ds = afgl_1986.to_xarray(df=df, name=name.value)
    expected_attrs = ["convention", "title", "source", "history", "references"]
    assert all([attr in ds.attrs for attr in expected_attrs])


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_find_name(name: afgl_1986.Name) -> None:
    """Returns name object corresponding to name str."""
    assert afgl_1986.find_name(name.value) == name


def test_find_name_invalid() -> None:
    """Raises a ValueError when an invalid name is provided."""
    with pytest.raises(ValueError):
        afgl_1986.find_name("invalid_name")


@pytest.mark.parametrize("name", [n for n in afgl_1986.Name])
def test_read(name: afgl_1986.Name) -> None:
    """Is equivalent to calling parse and then to_xarray."""
    df = afgl_1986.parse(name=name)
    ds = afgl_1986.to_xarray(df=df, name=name.value)
    assert ds == afgl_1986.read(name=name.value)
