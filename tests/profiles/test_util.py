import numpy as np
import numpy.testing as npt
import pytest
import xarray as xr

from joseki.profiles.util import (
    air_molar_mass_from_mass_fraction,
    molar_mass,
    number_density,
)
from joseki.units import to_quantity
from joseki import unit_registry as ureg

@pytest.fixture
def test_y():
    return xr.DataArray(
        data=np.atleast_2d(
            np.stack(
                [
                    [0.71, 0.71, 0.71],
                    [0.29, 0.29, 0.29],
                ]
            )
        ),
        coords={
            "m": ("m", ["N2", "O2"]),
            "z": ("z", [0, 50, 100], {"units": "km"}),
        }
    )


def test_air_molar_mass_from_mass_fraction(test_y):
    air_mm = air_molar_mass_from_mass_fraction(y=test_y)
    q = to_quantity(air_mm)
    assert q.check("[mass] / [substance]")
    assert np.allclose(air_mm.values, 29.0, rtol=1e-2)

def test_number_density():
    p = 101325 * ureg.Pa
    t = 273.15 * ureg.K
    n = number_density(p, t)
    assert n.check("[length]**-3")
    npt.assert_allclose(
        n.m_as("m^-3"),
        2.6867805e25,
        rtol=1e-5,
    )

def test_molar_mass():
    molecules = ["H2O", "CO2"]
    da = molar_mass(molecules)
    assert isinstance(da, xr.DataArray)
    q = to_quantity(da)
    assert q.check("[mass] / [substance]")

