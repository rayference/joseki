"""Test cases for the core module."""
import pathlib
import typing as t

import numpy as np
import pytest
import xarray as xr

from joseki import unit_registry as ureg
from joseki.afgl_1986 import Identifier as AFGL1986Identifier
from joseki.afgl_1986 import read as afgl_1986_read
from joseki.core import convert_to_identifier
from joseki.core import Identifier
from joseki.core import interp
from joseki.core import make
from joseki.core import represent_profile_in_cells


IDENTIFIER_CHOICES = [
    Identifier.AFGL_1986_TROPICAL,
    Identifier.RFM_WIN,
    "afgl_1986-tropical",
    "rfm-win",
]


@pytest.fixture
def test_data_set() -> xr.Dataset:
    """Test data set fixture."""
    return afgl_1986_read(identifier=AFGL1986Identifier.TROPICAL)


def test_interp_returns_data_set(test_data_set: xr.Dataset) -> None:
    """Returns an xarray.Dataset."""
    interpolated = interp(
        ds=test_data_set,
        z_new=np.linspace(0, 120, 121) * ureg.km,
    )
    assert isinstance(interpolated, xr.Dataset)  # type: ignore


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


def test_make_altitudes(tmpdir: t.Any) -> None:
    """Assigns data set' altitude values from file."""
    z_values = np.linspace(0, 120, 121)
    path = pathlib.Path(tmpdir, "z.txt")
    np.savetxt(path, z_values)  # type: ignore[no-untyped-call]
    ds = make(identifier="afgl_1986-tropical", altitudes=path)
    assert np.allclose(ds.z.values, z_values)


@pytest.mark.parametrize(
    "identifier",
    [
        Identifier.AFGL_1986_TROPICAL,
        Identifier.AFGL_1986_MIDLATITUDE_SUMMER,
        Identifier.AFGL_1986_MIDLATITUDE_WINTER,
        Identifier.AFGL_1986_SUBARCTIC_SUMMER,
        Identifier.AFGL_1986_SUBARCTIC_WINTER,
        Identifier.AFGL_1986_US_STANDARD,
    ],
)
def test_make_additional_molecules_false(identifier: Identifier) -> None:
    """Additional molecules not included when additional_molecules=False."""
    ds = make(identifier=identifier, additional_molecules=False)
    assert ds.m.size == 7


@pytest.mark.parametrize(
    "identifier",
    [
        Identifier.AFGL_1986_TROPICAL,
        Identifier.AFGL_1986_MIDLATITUDE_SUMMER,
        Identifier.AFGL_1986_MIDLATITUDE_WINTER,
        Identifier.AFGL_1986_SUBARCTIC_SUMMER,
        Identifier.AFGL_1986_SUBARCTIC_WINTER,
        Identifier.AFGL_1986_US_STANDARD,
    ],
)
def test_make_additional_molecules_true(identifier: Identifier) -> None:
    """Additional molecules are included when additional_molecules=True."""
    ds = make(identifier=identifier, additional_molecules=True)
    assert ds.m.size == 28


def test_convert_to_identifier() -> None:
    """rfm-mls is converted to Identifier.RFM_MLS."""
    assert convert_to_identifier("rfm-mls") == Identifier.RFM_MLS


def test_convert_to_identifier_unknown() -> None:
    """Unknown identifier raises ValueError."""
    with pytest.raises(ValueError):
        convert_to_identifier("unknown_identifier")
