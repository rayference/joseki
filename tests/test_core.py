"""Test cases for the core module."""
import pathlib
from typing import Any

import numpy as np
import pytest
import xarray as xr

from joseki.afgl_1986 import Identifier as AFGL1986Identifier
from joseki.afgl_1986 import read as afgl_1986_read
from joseki.core import Identifier
from joseki.core import interp
from joseki.core import make
from joseki.core import represent_profile_in_cells


IDENTIFIER_CHOICES = [i for i in Identifier]


@pytest.fixture
def test_data_set() -> xr.Dataset:
    """Test data set fixture."""
    return afgl_1986_read(identifier=AFGL1986Identifier.TROPICAL)


def test_interp_returns_data_set(test_data_set: xr.Dataset) -> None:
    """Returns an xarray.Dataset."""
    interpolated = interp(ds=test_data_set, z_new=np.linspace(0, 120, 121))
    assert isinstance(interpolated, xr.Dataset)


def test_interp_out_of_bound(test_data_set: xr.Dataset) -> None:
    """Raises when out of bounds values are provided."""
    with pytest.raises(ValueError):
        interp(ds=test_data_set, z_new=np.linspace(0, 150))


def test_represent_profile_in_cells(test_data_set: xr.Dataset) -> None:
    """Returns a xarray.Dataset object."""
    interpolated = represent_profile_in_cells(ds=test_data_set)
    assert isinstance(interpolated, xr.Dataset)


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make(identifier: Identifier) -> None:
    """Returns xr.Dataset."""
    assert isinstance(make(identifier=identifier), xr.Dataset)


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make_represent_in_cells(identifier: Identifier) -> None:
    """Returned data set has dimensions zbv and z and data variable z_bounds."""
    ds = make(
        identifier=identifier,
        represent_in_cells=True,
    )
    for dim in ["zbv", "z"]:
        assert dim in ds.dims
    assert "z_bounds" in ds.data_vars


@pytest.mark.parametrize(
    "identifier",
    IDENTIFIER_CHOICES,
)
def test_make_altitudes(tmpdir: Any, identifier: Identifier) -> None:
    """Assigns data set' altitude values from file."""
    z_values = np.linspace(0, 120, 121)
    path = pathlib.Path(tmpdir, "z.txt")
    np.savetxt(path, z_values)  # type: ignore[no-untyped-call]
    ds = make(identifier=identifier, altitudes=path)
    assert np.allclose(ds.zn.values, z_values)


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
    assert ds.molecules.size == 7


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
    assert ds.molecules.size == 28
