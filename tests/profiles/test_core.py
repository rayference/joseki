import numpy as np
import pytest
import xarray as xr

from joseki import unit_registry as ureg
from joseki.core import make
from joseki.profiles.core import interp
from joseki.core import represent_profile_in_cells


@pytest.fixture
def test_data_set() -> xr.Dataset:
    """Test dataset fixture."""
    return make(identifier="afgl_1986-tropical")


def test_interp_returns_data_set(test_data_set: xr.Dataset) -> None:
    """Returns an xarray.Dataset."""
    interpolated = interp(
        ds=test_data_set,
        z_new=np.linspace(0, 120, 121) * ureg.km,
    )
    assert isinstance(interpolated, xr.Dataset)


def test_interp_out_of_bound(test_data_set: xr.Dataset) -> None:
    """Raises when out of bounds values are provided."""
    with pytest.raises(ValueError):
        interp(ds=test_data_set, z_new=np.linspace(0, 150) * ureg.km)


def test_represent_profile_in_cells(test_data_set: xr.Dataset) -> None:
    """Returns a xarray.Dataset object."""
    interpolated = represent_profile_in_cells(ds=test_data_set)
    assert isinstance(interpolated, xr.Dataset)


def test_represent_profile_in_cells_twice(test_data_set: xr.Dataset) -> None:
    """Running function twice has no effect."""
    ds1 = represent_profile_in_cells(ds=test_data_set)
    ds2 = represent_profile_in_cells(ds=ds1)
    assert ds1 == ds2