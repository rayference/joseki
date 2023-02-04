"""Test cases for the accessor module."""
import numpy as np
import pytest
import xarray as xr

import joseki
from joseki.accessor import _scaling_factor
from joseki.units import to_quantity
from joseki.units import ureg


@pytest.fixture
def test_dataset() -> xr.Dataset:  # type: ignore[no-any-return]
    """Test dataset fixture."""
    return joseki.make("afgl_1986-us_standard")


@pytest.fixture
def test_dataset_in_cells() -> xr.Dataset:  # type: ignore[no-any-return]
    """Test dataset (with represent_in_cells=True) fixture."""
    return joseki.make("afgl_1986-us_standard", represent_in_cells=True)


def test_column_mass_density(test_dataset: xr.Dataset) -> None:
    """Column mass density of water vapor in us_standard is 14.27 kg/m^2."""
    water_vapor_amount = test_dataset.joseki.column_mass_density["H2O"]
    assert np.isclose(
        water_vapor_amount,
        14.27 * ureg.kg / ureg.m**2,
        rtol=1e-2,
    )


def test_column_mass_density_in_cells(test_dataset_in_cells: xr.Dataset) -> None:
    """Column mass density of water vapor in us_standard is 14.27 kg/m^2."""
    water_vapor_amount = test_dataset_in_cells.joseki.column_mass_density["H2O"]
    assert np.isclose(
        water_vapor_amount,
        14.27 * ureg.kg / ureg.m**2,
        rtol=1e-2,
    )


def test_column_number_density(test_dataset: xr.Dataset) -> None:
    """Column number density of ozone in us_standard is 348 dobson units."""
    ozone_amount = test_dataset.joseki.column_number_density["O3"]
    assert np.isclose(
        ozone_amount,
        348 * ureg.dobson_unit,
        rtol=1e-2,
    )


def test_column_number_density_in_cells(test_dataset_in_cells: xr.Dataset) -> None:
    """Column number density of ozone in us_standard is 348 dobson units."""
    ozone_amount = test_dataset_in_cells.joseki.column_number_density["O3"]
    assert np.isclose(
        ozone_amount,
        348 * ureg.dobson_unit,
        rtol=1e-2,
    )


def test_number_density_at_sea_level(test_dataset: xr.Dataset) -> None:
    """Number density at sea level of CO2 in us_standard matches dataset values."""
    carbon_dioxide_amount = test_dataset.joseki.number_density_at_sea_level["CO2"]
    n = to_quantity(test_dataset.n.isel(z=0))
    x_co2 = to_quantity(test_dataset.x_CO2.isel(z=0))
    assert np.isclose(
        carbon_dioxide_amount,
        x_co2 * n,
        rtol=1e-2,
    )


def test_mass_density_at_sea_level(test_dataset: xr.Dataset) -> None:
    """Mass density at sea level of H2O in us_standard is 0.00590733 kg / m^3."""
    water_vapor_amount = test_dataset.joseki.mass_density_at_sea_level["H2O"]
    assert np.isclose(
        water_vapor_amount,
        0.00590733 * ureg.kg / ureg.m**3,
        rtol=1e-2,
    )


def test_volume_fraction_at_sea_level(test_dataset: xr.Dataset) -> None:
    """CO2 volume mixing fraction at sea level in us_standard is 0.000333."""
    assert (
        test_dataset.joseki.volume_fraction_at_sea_level["CO2"]
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


def test_scaling_factors(test_dataset: xr.Dataset) -> None:
    """Scaling factors keys match target amounts keys."""
    target = {
        "H2O": 20.0 * ureg.kg * ureg.m**-2,
        "O3": 350.0 * ureg.dobson_unit,
    }
    factors = test_dataset.joseki.scaling_factors(target=target)
    assert all([k1 == k2 for k1, k2 in zip(target.keys(), factors.keys())])


def test_rescale(test_dataset: xr.Dataset) -> None:
    """Scaling factors are applied."""
    factors = {
        "H2O": 0.8,
        "CO2": 1.9,
    }
    initial = test_dataset.copy(deep=True)
    test_dataset.joseki.rescale(factors)
    assert all(
        [
            np.allclose(
                test_dataset[f"x_{m}"],
                factors[m] * initial[f"x_{m}"],
            )
            for m in factors
        ]
    )


def test_rescale_invalid(test_dataset: xr.Dataset) -> None:
    """A UserWarning is raised if invalid scaling factors are passed."""
    with pytest.raises(ValueError):
        test_dataset.joseki.rescale(factors={"O2": 2.0})
