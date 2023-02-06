"""Test cases for the accessor module."""
import numpy as np
import pytest

import joseki
from joseki.accessor import _scaling_factor
from joseki.units import to_quantity
from joseki.units import ureg


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard"]
)
def test_column_mass_density(identifier: str) -> None:
    """Column mass density of water vapor in us_standard is 14.27 kg/m^2."""
    ds = joseki.make(identifier)
    water_vapor_amount = ds.joseki.column_mass_density["H2O"]
    assert np.isclose(
        water_vapor_amount,
        14.27 * ureg.kg / ureg.m**2,
        rtol=1e-2,
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard"]
)
def test_column_mass_density_in_cells(identifier: str) -> None:
    """Column mass density of water vapor in us_standard is 14.27 kg/m^2."""
    ds = joseki.make(identifier, represent_in_cells=True)
    water_vapor_amount = ds.joseki.column_mass_density["H2O"]
    assert np.isclose(
        water_vapor_amount,
        14.27 * ureg.kg / ureg.m**2,
        rtol=1e-2,
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard"]
)
def test_column_number_density(identifier: str) -> None:
    """Column number density of ozone in us_standard is 348 dobson units."""
    ds = joseki.make(identifier)
    ozone_amount = ds.joseki.column_number_density["O3"]
    assert np.isclose(
        ozone_amount,
        348 * ureg.dobson_unit,
        rtol=1e-2,
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard"]
)
def test_column_number_density_in_cells(identifier: str) -> None:
    """Column number density of ozone in us_standard is 348 dobson units."""
    ds = joseki.make(identifier, represent_in_cells=True)
    ozone_amount = ds.joseki.column_number_density["O3"]
    assert np.isclose(
        ozone_amount,
        348 * ureg.dobson_unit,
        rtol=1e-2,
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-midlatitude_summer", "mipas_2007-midlatitude_day"]
)
def test_number_density_at_sea_level(identifier: str) -> None:
    """Number density at sea level of CO2 in matches dataset values."""
    ds = joseki.make(identifier)
    carbon_dioxide_amount = ds.joseki.number_density_at_sea_level["CO2"]
    n = to_quantity(ds.n.isel(z=0))
    x_co2 = to_quantity(ds.x_CO2.isel(z=0))
    assert np.isclose(
        carbon_dioxide_amount,
        x_co2 * n,
        rtol=1e-2,
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard"]
)
def test_mass_density_at_sea_level(identifier: str) -> None:
    """Mass density at sea level of H2O in us_standard is 0.00590733 kg / m^3."""
    ds = joseki.make(identifier)
    water_vapor_amount = ds.joseki.mass_density_at_sea_level["H2O"]
    assert np.isclose(
        water_vapor_amount,
        0.00590733 * ureg.kg / ureg.m**3,
        rtol=1e-2,
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard"]
)
def test_volume_fraction_at_sea_level(identifier: str) -> None:
    """CO2 volume mixing fraction at sea level in us_standard is 0.000333."""
    ds = joseki.make(identifier)
    assert (
        ds.joseki.volume_fraction_at_sea_level["CO2"]
        == 0.000330 * ureg.dimensionless
    )


def test_scaling_factor() -> None:
    """Returns 2.0 when target amount is twice larger than initial amount."""
    initial = 5 * ureg.m
    target = 10 * ureg.m
    assert _scaling_factor(initial_amount=initial, target_amount=target) == 2.0


def test_scaling_factor_zero() -> None:
    """Returns 0.0 when target amount and initial amount are both zero."""
    initial = 0.0 * ureg.m
    target = 0.0 * ureg.m
    assert _scaling_factor(initial_amount=initial, target_amount=target) == 0.0


def test_scaling_factor_raises() -> None:
    """Raises when the initial amount is zero but not the target amount."""
    initial = 0 * ureg.m
    target = 10 * ureg.m
    with pytest.raises(ValueError):
        _scaling_factor(initial_amount=initial, target_amount=target)


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard", "mipas_2007-midlatitude_day"]
)
def test_scaling_factors(identifier: str) -> None:
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
def test_rescale(identifier: str) -> None:
    """Scaling factors are applied."""
    ds = joseki.make(identifier)
    factors = {
        "H2O": 0.8,
        "CO2": 1.9,
    }
    initial = ds.copy(deep=True)
    ds.joseki.rescale(factors)
    assert all(
        [
            np.allclose(
                ds[f"x_{m}"],
                factors[m] * initial[f"x_{m}"],
            )
            for m in factors
        ]
    )


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-us_standard", "mipas_2007-midlatitude_day"]
)
def test_rescale_invalid(identifier: str) -> None:
    """A UserWarning is raised if invalid scaling factors are passed."""
    ds = joseki.make(identifier)
    with pytest.raises(ValueError):
        ds.joseki.rescale(factors={"O2": 2.0})
