"""Test cases for the core module."""
import numpy as np
import pytest
import xarray as xr

from joseki import unit_registry as ureg
from joseki.core import make


def test_make() -> None:
    """Returns xr.Dataset."""
    assert isinstance(make(identifier="afgl_1986-tropical"), xr.Dataset)


def test_make_represent_in_cells() -> None:
    """Returned data set has dimensions zbv and z and data variable z_bounds."""
    ds = make(
        identifier="afgl_1986-tropical",
        represent_in_cells=True,
    )
    for dim in ["zbv", "z"]:
        assert dim in ds.dims
    assert "z_bounds" in ds.data_vars


def test_make_altitudes() -> None:
    """Assigns data set' altitude values from file."""
    z = np.linspace(0, 120, 121) * ureg.km
    ds = make(identifier="afgl_1986-tropical", z=z)
    assert np.allclose(ds.z.values, z.m_as(ds.z.attrs["units"]))


@pytest.mark.parametrize(
    "identifier",
    [
        "afgl_1986-tropical",
        "afgl_1986-midlatitude_summer",
        "afgl_1986-midlatitude_winter",
        "afgl_1986-subarctic_summer",
        "afgl_1986-subarctic_winter",
        "afgl_1986-us_standard",
    ],
)
def test_make_additional_molecules_false(identifier: str) -> None:
    """Additional molecules not included when additional_molecules=False."""
    ds = make(identifier=identifier, additional_molecules=False)
    assert len(ds.joseki.molecules) == 7


@pytest.mark.parametrize(
    "identifier",
    [
        "afgl_1986-tropical",
        "afgl_1986-midlatitude_summer",
        "afgl_1986-midlatitude_winter",
        "afgl_1986-subarctic_summer",
        "afgl_1986-subarctic_winter",
        "afgl_1986-us_standard",
    ],
)
def test_make_additional_molecules_true(identifier: str) -> None:
    """Additional molecules are included when additional_molecules=True."""
    ds = make(identifier=identifier, additional_molecules=True)
    assert len(ds.joseki.molecules) == 28


def test_make_ussa_1976() -> None:
    """Returns dataset."""
    ds = make(identifier="ussa_1976")
    assert isinstance(ds, xr.Dataset)


def test_make_ussa_1976_z() -> None:
    """Returns dataset."""
    z = np.linspace(0.0, 100) * ureg.km
    ds = make(identifier="ussa_1976", z=z)
    assert isinstance(ds, xr.Dataset)
