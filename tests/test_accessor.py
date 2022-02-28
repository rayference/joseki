"""Test cases for the accessor module."""
import numpy as np
import pytest
import xarray as xr

import joseki
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
    x_co2 = to_quantity(test_dataset.x.sel(m="CO2").isel(z=0))
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


def test_rescale(test_dataset: xr.Dataset) -> None:
    """Scaling factors are applied."""
    factors = dict(
        H2O=0.8,
        CO2=1.9,
    )
    initial = test_dataset.copy(deep=True)
    test_dataset.joseki.rescale(factors)
    assert all(
        [
            np.allclose(
                test_dataset.x.sel(m=m),
                factors[m] * initial.x.sel(m=m),
            )
            for m in factors
        ]
    )


def test_rescale_invalid(test_dataset: xr.Dataset) -> None:
    """A UserWarning is raised if invalid scaling factors are passed."""
    factors = dict(O2=2)
    with pytest.raises(ValueError):
        test_dataset.joseki.rescale(factors)


def test_plot(test_dataset: xr.Dataset) -> None:
    """Does not raise."""
    test_dataset.joseki.plot(var="n")
