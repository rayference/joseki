import numpy as np
import pytest
import xarray as xr

from joseki.profiles.util import air_molar_mass_from_mass_fraction
from joseki.units import to_quantity

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