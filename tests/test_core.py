"""Test cases for the core module."""
import numpy as np
import pytest
from numpy.testing import assert_approx_equal

from joseki import unit_registry as ureg
from joseki.core import make, open_dataset, load_dataset, merge, identifiers


def test_make():
    """make returns a valid dataset."""
    ds = make(identifier="afgl_1986-tropical")
    assert ds.joseki.is_valid


def test_make_altitudes():
    """Assigns dataset' altitude values from file."""
    z = np.linspace(0, 120, 121) * ureg.km
    ds = make(identifier="afgl_1986-tropical", z=z)
    assert np.allclose(ds.z.values, z.m_as(ds.z.attrs["units"]))


def test_make_python_dict():
    """Pure Python dictionary can be used as input."""
    d = {
        "identifier": "afgl_1986-us_standard",
        "z": {
            "value": [0, 10, 20, 30, 60, 90, 120],
            "units": "km",
        }
    }
    ds = make(**d)
    assert ds.joseki.is_valid


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
    assert ds.joseki.is_valid


def test_make_ussa_1976_z():
    """Returns dataset."""
    z = np.linspace(0.0, 100) * ureg.km
    ds = make(identifier="ussa_1976", z=z)
    assert ds.joseki.is_valid


def test_make_conserve_column():
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

def test_make_molecules():
    """Returns dataset with molecules corresponding to selection."""
    ds = make(identifier="afgl_1986-tropical", molecules=["H2O", "CO2"])
    assert ds.joseki.molecules == ["H2O", "CO2"]


def test_make_regularize_bool():
    """Returns valid dataset with constant altitude step."""
    ds = make(identifier="afgl_1986-tropical", regularize=True)

    assert np.allclose(
        np.diff(ds.z.values),
        np.diff(ds.z.values)[0],
        rtol=1e-9,
        atol=1e-6,
    )
    assert ds.joseki.is_valid


def test_make_regularize_dict():
    """Returns valid dataset with constant altitude step."""
    num = 1201
    ds = make(
        identifier="afgl_1986-tropical",
        regularize={"options": {"num": num}},
    )

    assert ds.z.size == num


@pytest.mark.parametrize(
    "target",
    [
        {
            "H2O": 25 * ureg.kg / ureg.m**2
        },
        {
            "H2O": 25 * ureg.kg / ureg.m**2,
            "CO2": 420 * ureg.ppm
        },
        {
            "H2O": 25 * ureg.kg / ureg.m**2,
            "CO2": 420 * ureg.ppm,
            "O3": 350 * ureg.dobson_unit
        }
    ],
)
def test_make_rescale_to(target):
    ds = make(
        identifier="afgl_1986-tropical",
        rescale_to=target,
    )
    value = {
        "H2O": ds.joseki.column_mass_density["H2O"],
        "CO2": ds.joseki.mole_fraction_at_sea_level["CO2"],
        "O3": ds.joseki.column_number_density["O3"],
    }

    for molecule in target:
        assert_approx_equal(
            value[molecule].m_as(target[molecule].units),
            target[molecule].m,
            significant=6,
        )

def test_open_dataset(tmpdir):
    """Returns xr.Dataset."""
    ds = make(identifier="afgl_1986-tropical")
    path = tmpdir.join("test.nc")
    ds.to_netcdf(path)
    ds2 = open_dataset(path)
    assert ds2.joseki.is_valid


def test_load_dataset(tmpdir):
    """Returns xr.Dataset."""
    ds = make(identifier="afgl_1986-tropical")
    path = tmpdir.join("test.nc")
    ds.to_netcdf(path)
    ds2 = load_dataset(path)
    assert ds2.joseki.is_valid


def test_merge():
    ds1 = make(identifier="afgl_1986-tropical", molecules=["H2O", "CO2"])
    ds2 = make(identifier="afgl_1986-tropical", molecules=["O3"])
    ds = merge([ds1, ds2])
    assert ds.joseki.molecules == ["H2O", "CO2", "O3"]


def test_identifiers():
    """Returns list of identifiers."""
    assert isinstance(identifiers(), list)
