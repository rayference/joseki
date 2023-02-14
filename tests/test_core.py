"""Test cases for the core module."""
import numpy as np
import pytest
import xarray as xr
from numpy.testing import assert_approx_equal

from joseki import unit_registry as ureg
from joseki.core import make


def test_make():
    """Returns xr.Dataset."""
    assert isinstance(make(identifier="afgl_1986-tropical"), xr.Dataset)


def test_make_represent_in_cells():
    """Returned dataset has dimensions zbv and z and data variable z_bounds."""
    ds = make(
        identifier="afgl_1986-tropical",
        represent_in_cells=True,
    )
    for dim in ["zbv", "z"]:
        assert dim in ds.dims
    assert "z_bounds" in ds.data_vars


def test_make_altitudes():
    """Assigns dataset' altitude values from file."""
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
def test_make_additional_molecules_false(identifier: str):
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
def test_make_additional_molecules_true(identifier: str):
    """Additional molecules are included when additional_molecules=True."""
    ds = make(identifier=identifier, additional_molecules=True)
    assert len(ds.joseki.molecules) == 28


def test_make_ussa_1976():
    """Returns dataset."""
    ds = make(identifier="ussa_1976")
    assert isinstance(ds, xr.Dataset)


def test_make_ussa_1976_z():
    """Returns dataset."""
    z = np.linspace(0.0, 100) * ureg.km
    ds = make(identifier="ussa_1976", z=z)
    assert isinstance(ds, xr.Dataset)


def test_make_conserve_column_1():
    """Column densities are conserved when conserve_column is True."""
    ds0 = make(identifier="afgl_1986-us_standard")
    ds1 = make(
        identifier="afgl_1986-us_standard",
        z=np.linspace(0, 100, 21) * ureg.km,  # different than default
        conserve_column=True,
    )

    for m in ds0.joseki.molecules:
        assert_approx_equal(
            ds0.joseki.column_number_density[m].m,
            ds1.joseki.column_number_density[m].m,
            significant=6
        )

def test_make_conserve_column_2():
    """Column densities are conserved when conserve_column is True."""
    ds0 = make(identifier="afgl_1986-us_standard")
    ds1 = make(
        identifier="afgl_1986-us_standard",
        represent_in_cells=True,
        conserve_column=True,
    )

    for m in ds0.joseki.molecules:
        assert_approx_equal(
            ds0.joseki.column_number_density[m].m,
            ds1.joseki.column_number_density[m].m,
            significant=6
        )

def test_make_conserve_column_3():
    """Column densities are conserved when conserve_column is True."""
    ds0 = make(identifier="afgl_1986-us_standard")
    ds1 = make(
        identifier="afgl_1986-us_standard",
        z=np.linspace(0, 100, 21) * ureg.km,  # different than default
        represent_in_cells=True,
        conserve_column=True,
    )

    for m in ds0.joseki.molecules:
        assert_approx_equal(
            ds0.joseki.column_number_density[m].m,
            ds1.joseki.column_number_density[m].m,
            significant=6
        )