import numpy as np
import pint
import pytest
import xarray as xr
from numpy.testing import assert_approx_equal, assert_allclose

from joseki import unit_registry as ureg
from joseki.core import make
from joseki.profiles.core import (
    rescale_to_column,
    interp,
    extrapolate,
    regularize,
    select_molecules,
)
from joseki.units import to_quantity

@pytest.fixture
def test_data_set() -> xr.Dataset:
    """Test dataset fixture."""
    return make(identifier="afgl_1986-tropical")

def test_rescale_to_column_factor_0():
    ds = make(identifier="afgl_1986-tropical")
    with xr.set_options(keep_attrs=True):
        reference = ds.copy(deep=True).assign({
            "x_H2O": ds.x_H2O * 0
        })

    rescaled = rescale_to_column(
        reference=reference,
        ds=ds
    )

    assert_allclose(rescaled.x_H2O, 0)

def test_rescale_to_column_impossible():
    reference = make(identifier="afgl_1986-tropical")
    with xr.set_options(keep_attrs=True):
        ds = reference.copy(deep=True).assign({
            "x_H2O": reference.x_H2O * 0
        })

    with pytest.raises(ValueError):
        rescale_to_column(
            reference=reference,
            ds=ds
        )

def test_interp_returns_data_set(test_data_set: xr.Dataset):
    """Returns an xarray.Dataset."""
    interpolated = interp(
        ds=test_data_set,
        z_new=np.linspace(0, 120, 121) * ureg.km,
    )
    assert isinstance(interpolated, xr.Dataset)


def test_interp_out_of_bound(test_data_set: xr.Dataset):
    """Raises when out of bounds values are provided."""
    with pytest.raises(ValueError):
        interp(ds=test_data_set, z_new=np.linspace(0, 150) * ureg.km)


def test_interp_extrapolate(test_data_set: xr.Dataset):
    """Key-word argument 'fill_value' is processed."""
    interpolated = interp(
        ds=test_data_set,
        z_new=np.linspace(0, 150) * ureg.km,
        fill_value="extrapolate"
    )
    assert interpolated.joseki.is_valid

def test_interp_bounds_error(test_data_set: xr.Dataset):
    """Key-word argument 'fill_value' is processed."""
    interpolated = interp(
        ds=test_data_set,
        z_new=np.linspace(0, 100) * ureg.km,
        bounds_error=True,
    )
    assert interpolated.joseki.is_valid


@pytest.mark.parametrize(
    "z_down",
    [
        -0.1 * ureg.km,
        np.linspace(-0.5, -0.1, 5) * ureg.km,
    ]
)
def test_extrapolate_down(test_data_set: xr.Dataset, z_down: pint.Quantity):
    """Extrapolate down to 100 m."""
    extrapolated = extrapolate(
        ds=test_data_set,
        z_extra=z_down,
        direction="down",
    )

    # the last value of the z coordinate should be the same as z_down
    zunits = ureg.km
    assert_approx_equal(
        to_quantity(extrapolated.z).min().m_as(zunits),
        np.atleast_1d(z_down.m_as(zunits)).min(),
    )
    assert extrapolated.joseki.is_valid

@pytest.mark.parametrize(
    "z_up",
    [
        130 * ureg.km,
        np.linspace(130, 180, 6) * ureg.km,
    ]
)
def test_extrapolate_up(test_data_set: xr.Dataset, z_up: pint.Quantity):
    """Extrapolate up to 130 km."""
    z_up = 130.0 * ureg.km
    extrapolated = extrapolate(
        ds=test_data_set,
        z_extra=z_up,
        direction="up",
    )

    # the last value of the z coordinate should be the same as z_up
    zunits = ureg.km
    assert_approx_equal(
        to_quantity(extrapolated.z).max().m_as(zunits),
        np.atleast_1d(z_up.m_as(zunits)).max(),
    )
    assert extrapolated.joseki.is_valid


def test_extrapolate_invalid_altitude(test_data_set: xr.Dataset):
    """Raises when invalid altitude is provided."""
    with pytest.raises(ValueError):
        extrapolate(
            ds=test_data_set,
            z_extra=10 * ureg.km,
            direction="down",
        )
    
    with pytest.raises(ValueError):
        extrapolate(
            ds=test_data_set,
            z_extra=60 * ureg.km,
            direction="up",
        )

def test_extrapolate_invalid_direction(test_data_set: xr.Dataset):
    """Raises when invalid direction is provided."""
    with pytest.raises(ValueError):
        extrapolate(
            ds=test_data_set,
            z_extra=130 * ureg.km,
            direction="invalid",
        )

def test_regularize(test_data_set: xr.Dataset):
    """Regularize the profile."""
    regularized = regularize(ds=test_data_set)
    zgrid = to_quantity(regularized.z)

    # grid is regular
    assert np.all(np.diff(zgrid) == zgrid[1] - zgrid[0])

def test_regularize_zstep(test_data_set: xr.Dataset):
    """Regularize the profile."""
    zstep = 0.5 * ureg.km
    regularized = regularize(
        ds=test_data_set,
        options={
            "zstep": zstep,
        }
    )

    zgrid = to_quantity(regularized.z)
    assert np.all(np.diff(zgrid) == zstep)

def test_regularize_zstep_str_invalid(test_data_set: xr.Dataset):
    """Invalid zstep raises."""
    with pytest.raises(ValueError):
        regularize(
            ds=test_data_set,
            options={
                "zstep": "invalid",
            }
        )

def test_regularize_zstep_invalid_type(test_data_set: xr.Dataset):
    """Invalid zstep raises."""
    with pytest.raises(ValueError):
        regularize(
            ds=test_data_set,
            options={
                "zstep": ["cannot be a list"],
            }
        )

def test_regularize_options_invalid(test_data_set: xr.Dataset):
    """Invalid options raises."""
    with pytest.raises(ValueError):
        regularize(
            ds=test_data_set,
            options={}
        )


def test_regularize_num(test_data_set: xr.Dataset):
    """Regularize the profile."""
    num = 543
    regularized = regularize(
        ds=test_data_set,
        options={
            "num": num,
        }
    )

    assert regularized.z.size == num


def test_select_molecules(test_data_set: xr.Dataset):
    """Select molecules."""
    selected = select_molecules(
        ds=test_data_set,
        molecules=["H2O", "CO2"],
    )

    assert "H2O" in selected.joseki.molecules
    assert "CO2" in selected.joseki.molecules
    assert "O3" not in selected.joseki.molecules

def test_select_molecules_invalid(test_data_set: xr.Dataset):
    """Raise when selected molecules are not available."""
    molecules = ["SO2", "NO2"]
    ds = test_data_set.drop_vars([f"x_{m}" for m in molecules])
    with pytest.raises(ValueError):
        select_molecules(
            ds=ds,
            molecules=["H2O", "CO2", "SO2", "NO2"],
        )
