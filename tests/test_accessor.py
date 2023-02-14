"""Test cases for the accessor module."""
import numpy as np
import pint
import pytest
from numpy.testing import assert_approx_equal

import joseki
from joseki.accessor import _scaling_factor
from joseki.units import to_quantity
from joseki.units import ureg


def test_column_number_density_integration():
    """Same result is returned when profile is represented in cells or not."""
    ds1 = joseki.make("mipas_2007-midlatitude_day")
    ds2 = joseki.make("mipas_2007-midlatitude_day", represent_in_cells=True)
    assert_approx_equal(
        ds1.joseki.column_number_density["CO2"].m,
        ds2.joseki.column_number_density["CO2"].m,
        significant=5,
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
    "identifier, represent_in_cells, expected",
    [
        ("afgl_1986-us_standard", True, 14.27 * ureg.kg / ureg.m**2),
        ("afgl_1986-us_standard", False, 14.38 * ureg.kg / ureg.m**2),
        ("mipas_2007-midlatitude_day", True, 19.33 * ureg.kg / ureg.m**2),
        ("mipas_2007-midlatitude_day", False, 19.51 * ureg.kg / ureg.m**2),
    ]
)
def test_water_vapour_column_mass_density_in_cells(
    identifier: str,
    represent_in_cells: bool,
    expected: pint.Quantity
):
    """Column mass density of water vapor is close to expected values."""
    ds = joseki.make(identifier, represent_in_cells=represent_in_cells)
    water_vapor_amount = ds.joseki.column_mass_density["H2O"].to("kg/m^2")
    assert_approx_equal(water_vapor_amount.m, expected.m, significant=3)


@pytest.mark.parametrize(
    "identifier, represent_in_cells, expected",
    [
        ("afgl_1986-us_standard", True, 348.3 * ureg.dobson_unit),
        ("afgl_1986-us_standard", False, 345.7 * ureg.dobson_unit),
        ("mipas_2007-midlatitude_day", True, 303.4 * ureg.dobson_unit),
        ("mipas_2007-midlatitude_day", False, 301.7 * ureg.dobson_unit)
    ]
)
def test_column_number_density(
    identifier: str,
    represent_in_cells: bool,
    expected: pint.Quantity
):
    """Column number density of ozone matches expected value."""
    ds = joseki.make(identifier, represent_in_cells=represent_in_cells)
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
def test_volume_fraction_at_sea_level(identifier: str, expected):
    """CO2 volume mixing fraction at sea level matches expected value."""
    ds = joseki.make(identifier)
    value = ds.joseki.volume_fraction_at_sea_level["CO2"].to(ureg.dimensionless)
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
            check_volume_fraction_sum=True,
        )
