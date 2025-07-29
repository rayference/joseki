"""Test cases for the core module."""

import typing as t

import numpy as np
import pytest
import xarray as xr
from numpy.typing import NDArray

from joseki.profiles.ussa_1976.constants import AR_7, M0, O2_7, O_7, H, M
from joseki.profiles.ussa_1976.core import (
    SPECIES,
    VARIABLES,
    compute,
    compute_high_altitude,
    compute_levels_temperature_and_pressure_low_altitude,
    compute_low_altitude,
    compute_mean_molar_mass_high_altitude,
    compute_number_densities_high_altitude,
    compute_temperature_gradient_high_altitude,
    compute_temperature_high_altitude,
    init_data_set,
    to_altitude,
)


@pytest.fixture
def test_altitudes():
    """Test altitudes fixture."""
    return np.linspace(0.0, 100e3, 101)


def test_create(test_altitudes: NDArray[np.float64]):
    """Creates a data set with expected data."""
    ds = compute(z=test_altitudes)
    assert all([v in ds.data_vars for v in VARIABLES])

    variables = ["p", "t", "n", "n_tot"]
    ds = compute(z=test_altitudes, variables=variables)

    assert len(ds.dims) == 2
    assert "z" in ds.dims
    assert "s" in ds.dims
    assert len(ds.coords) == 2
    assert np.all(ds.z.values == test_altitudes)
    assert list(ds.s.values) == SPECIES
    assert all([var in ds for var in variables])
    assert all(
        [
            x in ds.attrs
            for x in ["convention", "title", "history", "source", "references"]
        ]
    )


def test_create_invalid_variables(
    test_altitudes: NDArray[np.float64],
):
    """Raises when invalid variables are given."""
    invalid_variables = ["p", "t", "invalid", "n"]
    with pytest.raises(ValueError):
        compute(z=test_altitudes, variables=invalid_variables)


def test_create_invalid_z():
    """Raises when invalid altitudes values are given."""
    with pytest.raises(ValueError):
        compute(z=np.array([-5.0]))  # value is negative

    with pytest.raises(ValueError):
        compute(z=np.array([1001e3]))  # value is larger than 1000 km


def test_create_below_86_km_layers_boundary_altitudes():
    """
    Produces correct results.

    We test the computation of the atmospheric variables (pressure,
    temperature and mass density) at the level altitudes, i.e. at the model
    layer boundaries. We assert correctness by comparing their values with the
    values from the table 1 of the U.S. Standard Atmosphere 1976 document.
    """
    z = to_altitude(H)
    ds = compute(z=z, variables=["p", "t", "rho"])

    level_temperature: NDArray[np.float64] = np.array(
        [288.15, 216.65, 216.65, 228.65, 270.65, 270.65, 214.65, 186.87]
    )
    level_pressure: NDArray[np.float64] = np.array(
        [101325.0, 22632.0, 5474.8, 868.01, 110.90, 66.938, 3.9564, 0.37338]
    )
    level_mass_density: NDArray[np.float64] = np.array(
        [
            1.225,
            0.36392,
            0.088035,
            0.013225,
            0.0014275,
            0.00086160,
            0.000064261,
            0.000006958,
        ]
    )

    assert np.allclose(ds.t.values, level_temperature, rtol=1e-4)
    assert np.allclose(ds.p.values, level_pressure, rtol=1e-4)
    assert np.allclose(ds.rho.values, level_mass_density, rtol=1e-3)


def test_create_below_86_km_arbitrary_altitudes():
    """
    Produces correct results.

    We test the computation of the atmospheric variables (pressure,
    temperature and mass density) at arbitrary altitudes. We assert correctness
    by comparing their values to the values from table 1 of the U.S. Standard
    Atmosphere 1976 document.
    """
    # The values below were selected arbitrarily from Table 1 of the document
    # such that there is at least one value in each of the 7 temperature
    # regions.
    h: NDArray[np.float64] = np.array(
        [
            200.0,
            1450.0,
            5250.0,
            6500.0,
            9800.0,
            17900.0,
            24800.0,
            27100.0,
            37200.0,
            40000.0,
            49400.0,
            61500.0,
            79500.0,
            84000.0,
        ]
    )
    temperatures: NDArray[np.float64] = np.array(
        [
            286.850,
            278.725,
            254.025,
            245.900,
            224.450,
            216.650,
            221.450,
            223.750,
            243.210,
            251.050,
            270.650,
            241.250,
            197.650,
            188.650,
        ]
    )
    pressures: NDArray[np.float64] = np.array(
        [
            98945.0,
            85076.0,
            52239.0,
            44034.0,
            27255.0,
            7624.1,
            2589.6,
            1819.4,
            408.7,
            277.52,
            81.919,
            16.456,
            0.96649,
            0.43598,
        ]
    )
    mass_densities: NDArray[np.float64] = np.array(
        [
            1.2017,
            1.0633,
            0.71641,
            0.62384,
            0.42304,
            0.12259,
            0.040739,
            0.028328,
            0.0058542,
            0.0038510,
            0.0010544,
            0.00023764,
            0.000017035,
            0.0000080510,
        ]
    )

    z = to_altitude(h)
    ds = compute(z=z, variables=["t", "p", "rho"])

    assert np.allclose(ds.t.values, temperatures, rtol=1e-4)
    assert np.allclose(ds.p.values, pressures, rtol=1e-4)
    assert np.allclose(ds.rho.values, mass_densities, rtol=1e-4)


@pytest.mark.parametrize(
    "z_bounds",
    [
        (0.0, 50e3),
        (120e3, 650e3),
        (70e3, 100e3),
    ],
)
def test_init_data_set(z_bounds: t.Tuple[float, float]):
    """Data set is initialized.

    Expected data variables are created and filled with nan values.
    Expected dimensions and coordinates are present.

    Parameters
    ----------
    z_bounds: tuple[float, float]
        Altitude bound values.
    """

    def check_data_set(ds: xr.Dataset):
        """Check a data set."""
        for var in VARIABLES:
            assert var in ds
            assert np.isnan(ds[var].values).all()

        assert ds.n.values.ndim == 2
        assert list(ds.s.values) == SPECIES

    z_start, z_stop = z_bounds
    z = np.linspace(z_start, z_stop)
    ds = init_data_set(z=z)
    check_data_set(ds)


def test_compute_levels_temperature_and_pressure_low_altitude():
    """Computes correct level temperature and pressure values.

    The correct values are taken from :cite:`NASA1976USStandardAtmosphere`.
    """
    tb, pb = compute_levels_temperature_and_pressure_low_altitude()

    level_temperature: NDArray[np.float64] = np.array(
        [288.15, 216.65, 216.65, 228.65, 270.65, 270.65, 214.65, 186.87]
    )
    level_pressure: NDArray[np.float64] = np.array(
        [101325.0, 22632.0, 5474.8, 868.01, 110.90, 66.938, 3.9564, 0.37338]
    )

    assert np.allclose(tb, level_temperature, rtol=1e-3)
    assert np.allclose(pb, level_pressure, rtol=1e-3)


def test_compute_number_density():
    """Computes correct number density values at arbitrary level altitudes.

    The correct values are taken from :cite:`NASA1976USStandardAtmosphere`
    (table VIII, p. 210-215).
    """
    # the following altitudes values are chosen arbitrarily
    altitudes: NDArray[np.float64] = np.array(
        [
            86e3,
            90e3,
            95e3,
            100e3,
            110e3,
            120e3,
            150e3,
            200e3,
            300e3,
            400e3,
            500e3,
            600e3,
            700e3,
            800e3,
            900e3,
            1000e3,
        ],
        dtype=np.float64,
    )

    mask = altitudes > 150e3

    # the corresponding number density values are from NASA (1976) - U.S.
    # Standard Atmosphere, table VIII (p. 210-215)
    values: t.Dict[str, NDArray[np.float64]] = {
        "N2": np.array(
            [
                1.13e20,
                5.547e19,
                2.268e19,
                9.210e18,
                1.641e18,
                3.726e17,
                3.124e16,
                2.925e15,
                9.593e13,
                4.669e12,
                2.592e11,
                1.575e10,
                1.038e9,
                7.377e7,
                5.641e6,
                4.626e5,
            ]
        ),
        "O": np.array(
            [
                O_7,
                2.443e17,
                4.365e17,
                4.298e17,
                2.303e17,
                9.275e16,
                1.780e16,
                4.050e15,
                5.443e14,
                9.584e13,
                1.836e13,
                3.707e12,
                7.840e11,
                1.732e11,
                3.989e10,
                9.562e9,
            ]
        ),
        "O2": np.array(
            [
                O2_7,
                1.479e19,
                5.83e18,
                2.151e18,
                2.621e17,
                4.395e16,
                2.750e15,
                1.918e14,
                3.942e12,
                1.252e11,
                4.607e9,
                1.880e8,
                8.410e6,
                4.105e5,
                2.177e4,
                1.251e3,
            ]
        ),
        "Ar": np.array(
            [
                AR_7,
                6.574e17,
                2.583e17,
                9.501e16,
                1.046e16,
                1.366e15,
                5.0e13,
                1.938e12,
                1.568e10,
                2.124e8,
                3.445e6,
                6.351e4,
                1.313e3,
                3.027e1,
                7.741e-1,
                2.188e-2,
            ]
        ),
        "He": np.array(
            [
                7.582e14,
                3.976e14,
                1.973e14,
                1.133e14,
                5.821e13,
                3.888e13,
                2.106e13,
                1.310e13,
                7.566e12,
                4.868e12,
                3.215e12,
                2.154e12,
                1.461e12,
                1.001e12,
                6.933e11,
                4.850e11,
            ]
        ),
        "H": np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                3.767e11,
                1.630e11,
                1.049e11,
                8.960e10,
                8.0e10,
                7.231e10,
                6.556e10,
                5.961e10,
                5.434e10,
                4.967e10,
            ]
        ),
    }

    n = compute_number_densities_high_altitude(altitudes=altitudes)

    assert np.allclose(n.sel(s="N2"), values["N2"], rtol=0.01)
    # TODO: investigate the poor relative tolerance that is achieved here
    assert np.allclose(n.sel(s="O"), values["O"], rtol=0.1)
    assert np.allclose(n.sel(s="O2"), values["O2"], rtol=0.01)
    assert np.allclose(n.sel(s="Ar"), values["Ar"], rtol=0.01)
    assert np.allclose(n.sel(s="He"), values["He"], rtol=0.01)
    assert np.allclose(n.sel(s="H")[mask], values["H"][mask], rtol=0.01)


def test_compute_mean_molar_mass():
    """Computes correct mean molar mass values.

    The correct values are taken from :cite:`NASA1976USStandardAtmosphere`.
    """
    z: NDArray[np.float64] = np.linspace(86e3, 1000e3, 915)
    assert np.allclose(
        compute_mean_molar_mass_high_altitude(z=z),
        np.where(z <= 100.0e3, M0, M["N2"]),
    )


def test_compute_temperature_above_86_km():
    """Compute correct temperature values.

    The correct values are taken from :cite:`NASA1976USStandardAtmosphere`.
    """
    z: NDArray[np.float64] = np.array([90e3, 100e3, 110e3, 120e3, 130e3, 200e3, 500e3])
    assert np.allclose(
        compute_temperature_high_altitude(z=z),
        np.array([186.87, 195.08, 240.00, 360.0, 469.27, 854.56, 999.24]),
        rtol=1e-3,
    )


def test_compute_temperature_above_86_km_invalid_altitudes():
    """Raises when altitude is out of range."""
    with pytest.raises(ValueError):
        compute_temperature_high_altitude(z=np.array([10e3]))  # 10 km < 86 km


def test_compute_high_altitude_no_mask():
    """Returns a Dataset."""
    z: NDArray[np.float64] = np.linspace(86e3, 1000e3)
    ds = init_data_set(z=z)
    compute_high_altitude(data_set=ds, mask=None, inplace=True)
    assert isinstance(ds, xr.Dataset)


def test_compute_high_altitude_not_inplace():
    """Returns a Dataset."""
    z: NDArray[np.float64] = np.linspace(86e3, 1000e3)
    ds1 = init_data_set(z=z)
    ds2 = compute_high_altitude(data_set=ds1, mask=None, inplace=False)
    assert ds1 != ds2
    assert isinstance(ds2, xr.Dataset)


def test_compute_low_altitude():
    """Returns a Dataset."""
    z: NDArray[np.float64] = np.linspace(0.0, 86e3)
    ds = init_data_set(z=z)
    compute_low_altitude(data_set=ds, mask=None, inplace=True)
    assert isinstance(ds, xr.Dataset)


def test_compute_low_altitude_not_inplace():
    """Returns a Dataset."""
    z: NDArray[np.float64] = np.linspace(0.0, 86e3)
    ds1 = init_data_set(z=z)
    ds2 = compute_low_altitude(data_set=ds1, mask=None, inplace=False)
    assert ds1 != ds2
    assert isinstance(ds2, xr.Dataset)


def test_compute_temperature_gradient_high_altitude():
    """Raises ValueError when altitude is out of bounds."""
    with pytest.raises(ValueError):
        compute_temperature_gradient_high_altitude(z=np.array([1300e3]))
