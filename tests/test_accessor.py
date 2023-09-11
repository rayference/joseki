"""Test cases for the accessor module."""
import numpy as np
import pint
import pytest
import xarray as xr
from numpy.testing import assert_approx_equal

import joseki
from joseki.accessor import _scaling_factor
from joseki.units import to_quantity
from joseki.units import ureg


@pytest.fixture
def test_dataset_non_standard_units():
    """Returns a test dataset."""
    return xr.Dataset(
        {
            "p": (
                "z",
                np.linspace(0, 100, 10),
                {
                    "units": "bar",
                    "standard_name": "air_pressure",
                    "long_name": "pressure",
                },
            ),
            "t": (
                "z",
                np.linspace(0, 100, 10),
                {
                    "units": "millikelvin",
                    "standard_name": "air_temperature",
                    "long_name": "temperature",
                },
            ),
            "n": (
                "z",
                np.linspace(0, 100, 10),
                {
                    "units": "cm ^ -3",
                    "standard_name": "air_number_density",
                    "long_name": "number density",
                },
            ),
            "x_H2O": (
                "z",
                np.linspace(0, 1, 10),
                {
                    "units": "ppmv",
                    "standard_name": "H2O_mole_fraction",
                    "long_name": "H2O mole fraction",
                },
            ),
        },
        coords={
            "z": (
                "z",
                np.linspace(0, 100, 10),
                {
                    "units": "hm",
                    "standard_name": "altitude",
                    "long_name": "altitude",
                },
            ),
        },
        attrs={
            "Conventions": "CF-1.10",
            "title": "Test dataset",
            "institution": "Rayference",
            "source": "N/A",
            "history": "N/A",
            "references": "N/A",
            "url": "N/A",
            "urldate": "N/A",
        }
    )


@pytest.mark.parametrize(
    "identifier",
    ["ussa_1976", "afgl_1986-us_standard", "mipas_2007-midlatitude_day"]
)
def test_column_mass_density(identifier: str):
    """Returns a dictionary."""
    ds = joseki.make(identifier)
    assert isinstance(ds.joseki.column_mass_density, dict)


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("afgl_1986-us_standard", 14.38 * ureg.kg / ureg.m**2),
        ("mipas_2007-midlatitude_day", 19.51 * ureg.kg / ureg.m**2),
    ]
)
def test_water_vapour_column_mass_density_in_cells(
    identifier: str,
    expected: pint.Quantity
):
    """Column mass density of water vapor is close to expected values."""
    ds = joseki.make(identifier)
    water_vapor_amount = ds.joseki.column_mass_density["H2O"].to("kg/m^2")
    assert_approx_equal(water_vapor_amount.m, expected.m, significant=3)


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("afgl_1986-us_standard", 345.7 * ureg.dobson_unit),
        ("mipas_2007-midlatitude_day", 301.7 * ureg.dobson_unit)
    ]
)
def test_column_number_density(
    identifier: str,
    expected: pint.Quantity
):
    """Column number density of ozone matches expected value."""
    ds = joseki.make(identifier)
    ozone_amount = ds.joseki.column_number_density["O3"].to("dobson_unit")
    assert_approx_equal(ozone_amount.m, expected.m, significant=3)


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-midlatitude_summer", "mipas_2007-midlatitude_day"]
)
def test_number_density_at_sea_level(identifier: str):
    """Number density at sea level of CO2 in matches dataset values."""
    ds = joseki.make(identifier)
    carbon_dioxide_amount = ds.joseki.number_density_at_sea_level["CO2"]
    n = to_quantity(ds.n.isel(z=0))
    x_co2 = to_quantity(ds.x_CO2.isel(z=0))
    expected = (x_co2 * n).to("m^-3")
    value = carbon_dioxide_amount.to("m^-3")
    assert_approx_equal(value.m, expected.m)


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("afgl_1986-us_standard", 0.00590723 * ureg.kg / ureg.m**3),
        ("mipas_2007-midlatitude_day", 0.00901076 * ureg.kg / ureg.m**3)
    ]
)
def test_mass_density_at_sea_level(identifier: str, expected: pint.Quantity):
    """Mass density at sea level of H2O matches expected value."""
    ds = joseki.make(identifier)
    water_vapor_amount = ds.joseki.mass_density_at_sea_level["H2O"].to("kg/m^3")
    assert_approx_equal(water_vapor_amount.m, expected.m, significant=6)


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("afgl_1986-us_standard", 0.000330 * ureg.dimensionless),
        ("mipas_2007-midlatitude_day", 0.0003685 * ureg.dimensionless)
    ]
)
def test_mole_fraction_at_sea_level(identifier: str, expected):
    """CO2 mole mixing fraction at sea level matches expected value."""
    ds = joseki.make(identifier)
    value = ds.joseki.mole_fraction_at_sea_level["CO2"].to(ureg.dimensionless)
    assert_approx_equal(value.m, expected.m)


def test_scaling_factor():
    """Returns 2.0 when target amount is twice larger than initial amount."""
    initial = 5 * ureg.m
    target = 10 * ureg.m
    assert _scaling_factor(initial_amount=initial, target_amount=target) == 2.0


def test_scaling_factor_zero():
    """Returns 0.0 when target amount and initial amount are both zero."""
    initial = 0.0 * ureg.m
    target = 0.0 * ureg.m
    assert _scaling_factor(initial_amount=initial, target_amount=target) == 0.0


def test_scaling_factor_raises():
    """Raises when the initial amount is zero but not the target amount."""
    initial = 0 * ureg.m
    target = 10 * ureg.m
    with pytest.raises(ValueError):
        _scaling_factor(initial_amount=initial, target_amount=target)


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard", "mipas_2007-midlatitude_day"]
)
def test_scaling_factors(identifier: str):
    """Scaling factors keys match target amounts keys."""
    ds = joseki.make(identifier)
    target = {
        "H2O": 20.0 * ureg.kg * ureg.m**-2,
        "O3": 350.0 * ureg.dobson_unit,
    }
    factors = ds.joseki.scaling_factors(target=target)
    assert all([k1 == k2 for k1, k2 in zip(target.keys(), factors.keys())])


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard"]
)
def test_rescale(identifier: str):
    """Scaling factors are applied."""
    ds = joseki.make(identifier)
    factors = {
        "H2O": 0.8,
        "CO2": 1.9,
    }
    initial = ds.copy(deep=True)
    rescaled = ds.joseki.rescale(factors)
    assert all(
        [
            np.allclose(
                rescaled[f"x_{m}"],
                factors[m] * initial[f"x_{m}"],
            )
            for m in factors
        ]
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard", "mipas_2007-midlatitude_day"]
)
def test_rescale_invalid(identifier: str):
    """A UserWarning is raised if invalid scaling factors are passed."""
    ds = joseki.make(identifier)
    with pytest.raises(ValueError):
        ds.joseki.rescale(
            factors={"O2": 2.0},
            check_x_sum=True,
        )

def test_rescale_to_column_mass_density():
    """Column mass density of H2O matches target value."""
    ds = joseki.make("afgl_1986-midlatitude_summer")
    target = {
        "H2O": 20.0 * ureg.kg * ureg.m**-2,
    }
    rescaled = ds.joseki.rescale_to(target)
    assert_approx_equal(
        rescaled.joseki.column_mass_density["H2O"].m,
        target["H2O"].m,
        significant=3,
    )

@pytest.mark.parametrize(
    "molecules",
    [
        ["H2O"],
        ["H2O", "CO2"],
    ]
)
def test_drop_molecules(molecules):
    """x_M data variable is(are) dropped."""
    ds = joseki.make("afgl_1986-midlatitude_summer")
    assert all([m in ds.joseki.molecules for m in molecules])
    dropped = ds.joseki.drop_molecules(molecules)
    assert all([m not in dropped.joseki.molecules for m in molecules])

def test_valid_True():
    """Returns True if the dataset is valid."""
    ds = joseki.make("afgl_1986-midlatitude_summer")
    assert ds.joseki.is_valid

def test_valid_False():
    """Returns False if the dataset is not valid."""
    ds = joseki.make("afgl_1986-midlatitude_summer")
    
    # drop variable 't'
    ds = ds.drop_vars("t")

    assert not ds.joseki.is_valid

def test_validate(test_dataset_non_standard_units, tmpdir):
    """Returns True if the dataset is valid."""
    path = tmpdir.join("test_dataset.nc")
    test_dataset_non_standard_units.to_netcdf(path)
    loaded = joseki.load_dataset(path)
    assert loaded.joseki.is_valid
