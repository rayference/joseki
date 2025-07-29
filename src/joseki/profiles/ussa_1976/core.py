"""
U.S. Standard Atmosphere 1976 thermophysical model.

The U.S. Standard Atmosphere 1976 model :cite:`NASA1976USStandardAtmosphere`
divides the atmosphere into two altitude regions:

1. the low-altitude region, from 0 to 86 kilometers
2. the high-altitude region, from 86 to 1000 kilometers.

A number of computational functions hereafter are specialized for one or
the other altitude region and is valid only in that altitude region, not in
the other.
Their name include a ``low_altitude`` or a ``high_altitude`` part to reflect
that they are valid only in the low altitude region and high altitude region,
respectively.
"""

# IMPORTANT: This is a quick port of the external ussa1976 package, which is
# no longer maintained. The code was pasted here with minimal changes and has
# redundancies and inconsistencies with respect to the rest of the codebase.
# TODO: Refactor this module

import datetime
from typing import Callable, List, Optional, Tuple, Union

import numpy as np
import numpy.ma as ma
import xarray as xr
from numpy.typing import NDArray
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d

from .constants import (
    ALPHA,
    AR_7,
    BETA,
    G0,
    GAMMA,
    H_11,
    HE_7,
    K_7,
    LAMBDA,
    LK,
    LK7,
    LK9,
    M0,
    N2_7,
    NA,
    O2_7,
    O_7,
    P0,
    PHI,
    Q1,
    Q2,
    R0,
    SIGMA,
    T0,
    T7,
    T9,
    T10,
    T11,
    TINF,
    U1,
    U2,
    W1,
    W2,
    Z7,
    Z8,
    Z9,
    Z10,
    Z12,
    A,
    B,
    H,
    K,
    M,
    R,
    S,
)
from ..._version import __version__
from ...constants import F

# List of all gas species
SPECIES = [
    "N2",
    "O2",
    "Ar",
    "CO2",
    "Ne",
    "He",
    "Kr",
    "Xe",
    "CH4",
    "H2",
    "O",
    "H",
]

# List of variables computed by the model
VARIABLES = [
    "t",
    "p",
    "n",
    "n_tot",
    "rho",
    "mv",
    "hp",
    "v",
    "mfp",
    "f",
    "cs",
    "mu",
    "nu",
    "kt",
]

# Variables standard names with respect to the Climate and Forecast (CF)
# convention
STANDARD_NAME = {
    "t": "air_temperature",
    "p": "air_pressure",
    "n": "number_density",
    "n_tot": "air_number_density",
    "rho": "air_density",
    "mv": "air_molar_volume",
    "hp": "air_pressure_scale_height",
    "v": "air_particles_mean_speed",
    "mfp": "air_particles_mean_free_path",
    "f": "air_particles_mean_collision_frequency",
    "cs": "speed_of_sound_in_air",
    "mu": "air_dynamic_viscosity",
    "nu": "air_kinematic_viscosity",
    "kt": "air_thermal_conductivity_coefficient",
    "z": "altitude",
    "h": "geopotential_height",
}

# Variables long names
LONG_NAME = {
    "t": "air temperature",
    "p": "air pressure",
    "n": "number_density",
    "n_tot": "air number density",
    "rho": "air density",
    "mv": "air molar volume",
    "hp": "air pressure scale height",
    "v": "air particles mean speed",
    "mfp": "air particles mean free path",
    "f": "air particles mean collision frequency",
    "cs": "speed of sound in air",
    "mu": "air dynamic viscosity",
    "nu": "air kinematic viscosity",
    "kt": "air thermal conductivity coefficient",
    "z": "altitude",
    "h": "geopotential height",
}

# Units of relevant quantities
UNITS = {
    "t": "K",
    "p": "Pa",
    "n": "m^-3",
    "n_tot": "m^-3",
    "rho": "kg/m^3",
    "mv": "m^3/mole",
    "hp": "m",
    "v": "m/s",
    "mfp": "m",
    "f": "s^-1",
    "cs": "m/s",
    "mu": "kg/(m*s)",
    "nu": "m^2/s",
    "kt": "W/(m*K)",
    "z": "m",
    "h": "m",
    "s": "",
}

# Variables dimensions
DIMS = {
    "t": "z",
    "p": "z",
    "n": ("s", "z"),
    "n_tot": "z",
    "rho": "z",
    "mv": "z",
    "hp": "z",
    "v": "z",
    "mfp": "z",
    "f": "z",
    "cs": "z",
    "mu": "z",
    "nu": "z",
    "kt": "z",
}


DEFAULT_Z = np.concatenate(
    [
        np.arange(0.0, 11000.0, 50.0),
        np.arange(11000.0, 32000.0, 100.0),
        np.arange(32000.0, 50000.0, 200.0),
        np.arange(50000.0, 100000.0, 500.0),
        np.arange(100000.0, 300000.0, 1000.0),
        np.arange(300000.0, 500000.0, 2000.0),
        np.arange(500000.0, 1000001.0, 5000.0),
    ]
)


def compute(
    z: NDArray[np.float64] = DEFAULT_Z,
    variables: Optional[List[str]] = None,
) -> xr.Dataset:
    """Compute U.S. Standard Atmosphere 1976 data set on specified altitude grid.

    Parameters
    ----------
    z: array
        Altitude [m].

    variables: list, optional
        Names of the variables to compute.

    Returns
    -------
    Dataset
        Data set holding the values of the different atmospheric variables.

    Raises
    ------
    ValueError
        When altitude is out of bounds, or when variables are invalid.
    """
    if np.any(z < 0.0):
        raise ValueError("altitude values must be greater than or equal to zero")

    if np.any(z > 1000e3):
        raise ValueError("altitude values must be less then or equal to 1000 km")

    if variables is None:
        variables = VARIABLES
    else:
        for var in variables:
            if var not in VARIABLES:
                raise ValueError(var, " is not a valid variable name")

    # initialise data set
    ds = init_data_set(z=z)

    z_delim = 86e3

    # compute the model in the low-altitude region
    low_altitude_region = ds.z.values <= z_delim
    compute_low_altitude(data_set=ds, mask=low_altitude_region, inplace=True)

    # compute the model in the high-altitude region
    high_altitude_region = ds.z.values > z_delim
    compute_high_altitude(data_set=ds, mask=high_altitude_region, inplace=True)

    # replace all np.nan with 0.0 in number densities values
    n = ds.n.values
    n[np.isnan(n)] = 0.0
    ds.n.values = n

    # list names of variables to drop from the data set
    names = []
    for var in ds.data_vars:  # type: ignore
        if var not in variables:
            names.append(var)

    return ds.drop_vars(names)  # type: ignore


def compute_low_altitude(
    data_set: xr.Dataset,
    mask: Optional[NDArray[bool]] = None,  # type: ignore
    inplace: bool = False,
) -> Optional[xr.Dataset]:
    """Compute U.S. Standard Atmosphere 1976 in low-altitude region.

    Parameters
    ----------
    data_set: Dataset
        Data set to compute.

    mask: DataArray, optional
        Mask to select the region of the data set to compute.
        By default, the mask selects the entire data set.

    inplace: bool, default=False
        If ``True``, modifies ``data_set`` in place, else returns a copy of
        ``data_set``.

    Returns
    -------
    Dataset
        If ``inplace`` is ``True``, returns nothing, else returns a copy of
        ``data_set``.
    """
    if mask is None:
        mask = np.full_like(data_set.coords["z"].values, True, dtype=bool)

    if inplace:
        ds = data_set
    else:
        ds = data_set.copy(deep=True)

    z = ds.z[mask].values

    # compute levels temperature and pressure values
    tb, pb = compute_levels_temperature_and_pressure_low_altitude()

    # compute geopotential height, temperature and pressure
    h = to_geopotential_height(z)
    t = compute_temperature_low_altitude(h=h, tb=tb)
    p = compute_pressure_low_altitude(h=h, pb=pb, tb=tb)

    # compute the auxiliary atmospheric variables
    n_tot = NA * p / (R * t)
    rho = p * M0 / (R * t)
    g = compute_gravity(z)
    mu = BETA * np.power(t, 1.5) / (t + S)

    # assign data set with computed values
    ds["t"].loc[dict(z=z)] = t
    ds["p"].loc[dict(z=z)] = p
    ds["n_tot"].loc[dict(z=z)] = n_tot

    species = ["N2", "O2", "Ar", "CO2", "Ne", "He", "Kr", "Xe", "CH4", "H2"]
    for i, s in enumerate(SPECIES):
        if s in species:
            ds["n"][i].loc[dict(z=z)] = F[s] * n_tot

    ds["rho"].loc[dict(z=z)] = rho
    ds["mv"].loc[dict(z=z)] = NA / n_tot
    ds["hp"].loc[dict(z=z)] = R * t / (g * M0)
    ds["v"].loc[dict(z=z)] = np.sqrt(8.0 * R * t / (np.pi * M0))
    ds["mfp"].loc[dict(z=z)] = np.sqrt(2.0) / (
        2.0 * np.pi * np.power(SIGMA, 2.0) * n_tot
    )
    ds["f"].loc[dict(z=z)] = (
        4.0
        * NA
        * np.power(SIGMA, 2.0)
        * np.sqrt(np.pi * np.power(p, 2.0) / (R * M0 * t))
    )
    ds["cs"].loc[dict(z=z)] = np.sqrt(GAMMA * R * t / M0)
    ds["mu"].loc[dict(z=z)] = mu
    ds["nu"].loc[dict(z=z)] = mu / rho
    ds["kt"].loc[dict(z=z)] = (
        2.64638e-3 * np.power(t, 1.5) / (t + 245.4 * np.power(10.0, -12.0 / t))
    )

    if not inplace:
        return ds
    else:
        return None


def compute_high_altitude(
    data_set: xr.Dataset,
    mask: Optional[NDArray[bool]] = None,
    inplace: bool = False,
) -> Optional[xr.Dataset]:
    """Compute U.S. Standard Atmosphere 1976 in high-altitude region.

    Parameters
    ----------
    data_set: Dataset
        Data set to compute.

    mask: DataArray, optional
        Mask to select the region of the data set to compute.
        By default, the mask selects the entire data set.

    inplace: bool, default False
        If ``True``, modifies ``data_set`` in place, else returns a copy of
        ``data_set``.

    Returns
    -------
    Dataset
        If ``inplace`` is True, returns nothing, else returns a copy of
        ``data_set``.
    """
    if mask is None:
        mask = np.full_like(data_set.coords["z"].values, True, dtype=bool)

    if inplace:
        ds = data_set
    else:
        ds = data_set.copy(deep=True)

    z = ds.coords["z"][mask].values
    if len(z) == 0:
        return ds

    n = compute_number_densities_high_altitude(z)
    species = ["N2", "O", "O2", "Ar", "He", "H"]
    ni: NDArray[np.float64] = np.array([n.sel(s=s).values for s in species])
    n_tot = np.sum(ni, axis=0)
    fi = ni / n_tot[np.newaxis, :]
    mi: NDArray[np.float64] = np.array([M[s] for s in species])
    m = np.sum(fi * mi[:, np.newaxis], axis=0)
    t = compute_temperature_high_altitude(z)
    p = K * n_tot * t
    rho = np.sum(ni * mi[:, np.newaxis], axis=0) / NA
    g = compute_gravity(z)

    # assign data set with computed values
    ds["t"].loc[dict(z=z)] = t
    ds["p"].loc[dict(z=z)] = p
    ds["n_tot"].loc[dict(z=z)] = n_tot

    for i, s in enumerate(SPECIES):
        if s in species:
            ds["n"][i].loc[dict(z=z)] = n.sel(s=s).values

    ds["rho"].loc[dict(z=z)] = rho
    ds["mv"].loc[dict(z=z)] = NA / n_tot
    ds["hp"].loc[dict(z=z)] = R * t / (g * m)
    ds["v"].loc[dict(z=z)] = np.sqrt(8.0 * R * t / (np.pi * m))
    ds["mfp"].loc[dict(z=z)] = np.sqrt(2.0) / (
        2.0 * np.pi * np.power(SIGMA, 2.0) * n_tot
    )
    ds["f"].loc[dict(z=z)] = (
        4.0
        * NA
        * np.power(SIGMA, 2.0)
        * np.sqrt(np.pi * np.power(p, 2.0) / (R * m * t))
    )

    if not inplace:
        return ds
    else:
        return None


def init_data_set(z: NDArray[np.float64]) -> xr.Dataset:  # type: ignore
    """Initialise data set.

    Parameters
    ----------
    z: array
        Altitudes [m].

    Returns
    -------
    Dataset
        Initialised data set.
    """
    data_vars = {}
    for var in VARIABLES:
        if var != "n":
            data_vars[var] = (
                DIMS[var],
                np.full(z.shape, np.nan),
                {
                    "units": UNITS[var],
                    "long_name": LONG_NAME[var],
                    "standard_name": STANDARD_NAME[var],
                },
            )
        else:
            data_vars[var] = (
                DIMS[var],
                np.full((len(SPECIES), len(z)), np.nan),
                {
                    "units": UNITS[var],
                    "long_name": LONG_NAME[var],
                    "standard_name": STANDARD_NAME["n"],
                },
            )

    coords = {
        "z": (
            "z",
            z,
            {
                "standard_name": "altitude",
                "long_name": "altitude",
                "units": "m",
            },
        ),
        "s": ("s", SPECIES, {"long_name": "species", "standard_name": "species"}),
    }

    attrs = {
        "convention": "CF-1.9",
        "title": "U.S. Standard Atmosphere 1976",
        "history": (
            f"{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            f" - data set creation - ussa1976, version {__version__}"
        ),
        "source": f"ussa1976, version {__version__}",
        "references": (
            "U.S. Standard Atmosphere, 1976, NASA-TM-X-74335NOAA-S/T-76-1562"
        ),
    }

    return xr.Dataset(data_vars, coords, attrs)  # type: ignore


def compute_levels_temperature_and_pressure_low_altitude() -> Tuple[
    NDArray[np.float64], NDArray[np.float64]
]:
    """Compute temperature and pressure at low-altitude region' levels.

    Returns
    -------
    tuple of arrays:
        Levels temperatures [K] and pressures [Pa].
    """
    tb = [T0]
    pb = [P0]
    for i in range(1, len(H)):
        t_next = tb[i - 1] + LK[i - 1] * (H[i] - H[i - 1])
        tb.append(t_next)
        if LK[i - 1] == 0:
            p_next = compute_pressure_low_altitude_zero_gradient(
                h=H[i],
                hb=H[i - 1],
                pb=pb[i - 1],
                tb=tb[i - 1],
            )
        else:
            p_next = compute_pressure_low_altitude_non_zero_gradient(
                h=H[i],
                hb=H[i - 1],
                pb=pb[i - 1],
                tb=tb[i - 1],
                lkb=LK[i - 1],
            )
        pb.append(float(p_next))
    return np.array(tb, dtype=np.float64), np.array(pb, dtype=np.float64)


def compute_number_densities_high_altitude(
    altitudes: NDArray[np.float64],
) -> xr.DataArray:
    """Compute number density of individual species in high-altitude region.

    Parameters
    ----------
    altitudes: array
        Altitudes [m].

    Returns
    -------
    DataArray
        Number densities of the individual species and total number density at
        the given altitudes.

    Notes
    -----
    A uniform altitude grid is generated and used for the computation of the
    integral as well as for the computation of the number densities of the
    individual species. This gridded data is then interpolated at the query
    ``altitudes`` using a linear interpolation scheme in logarithmic space.
    """
    # altitude grid
    grid: NDArray[np.float64] = np.concatenate(
        (
            np.linspace(start=Z7, stop=150e3, num=640, endpoint=False),
            np.geomspace(start=150e3, stop=Z12, num=100, endpoint=True),
        )
    )

    # pre-computed variables
    m = compute_mean_molar_mass_high_altitude(z=grid)
    g = compute_gravity(z=grid)
    t = compute_temperature_high_altitude(z=grid)
    dt_dz = compute_temperature_gradient_high_altitude(z=grid)
    below_115 = grid < 115e3
    k = eddy_diffusion_coefficient(grid[below_115])

    n_grid = {}

    # *************************************************************************
    # Molecular nitrogen
    # *************************************************************************

    y = m * g / (R * t)  # m^-1
    n_grid["N2"] = N2_7 * (T7 / t) * np.exp(-cumulative_trapezoid(y, grid, initial=0.0))

    # *************************************************************************
    # Atomic oxygen
    # *************************************************************************

    d = thermal_diffusion_coefficient(
        nb=n_grid["N2"][below_115],
        t=t[below_115],
        a=A["O"],
        b=B["O"],
    )
    y = thermal_diffusion_term_atomic_oxygen(
        grid,
        g,
        t,
        dt_dz,
        d,
        k,
    ) + velocity_term_atomic_oxygen(grid)
    n_grid["O"] = O_7 * (T7 / t) * np.exp(-cumulative_trapezoid(y, grid, initial=0.0))

    # *************************************************************************
    # Molecular oxygen
    # *************************************************************************

    d = thermal_diffusion_coefficient(
        nb=n_grid["N2"][below_115],
        t=t[below_115],
        a=A["O2"],
        b=B["O2"],
    )
    y = thermal_diffusion_term(
        s="O2",
        z_grid=grid,
        g=g,
        t=t,
        dt_dz=dt_dz,
        m=m,
        d=d,
        k=k,
    ) + velocity_term("O2", grid)
    n_grid["O2"] = O2_7 * (T7 / t) * np.exp(-cumulative_trapezoid(y, grid, initial=0.0))

    # *************************************************************************
    # Argon
    # *************************************************************************

    background = (
        n_grid["N2"][below_115] + n_grid["O"][below_115] + n_grid["O2"][below_115]
    )
    d = thermal_diffusion_coefficient(
        nb=background,
        t=t[below_115],
        a=A["Ar"],
        b=B["Ar"],
    )
    y = thermal_diffusion_term(
        s="Ar",
        z_grid=grid,
        g=g,
        t=t,
        dt_dz=dt_dz,
        m=m,
        d=d,
        k=k,
    ) + velocity_term("Ar", grid)
    n_grid["Ar"] = AR_7 * (T7 / t) * np.exp(-cumulative_trapezoid(y, grid, initial=0.0))

    # *************************************************************************
    # Helium
    # *************************************************************************

    background = (
        n_grid["N2"][below_115] + n_grid["O"][below_115] + n_grid["O2"][below_115]
    )
    d = thermal_diffusion_coefficient(
        nb=background,
        t=t[below_115],
        a=A["He"],
        b=B["He"],
    )
    y = thermal_diffusion_term(
        s="He",
        z_grid=grid,
        g=g,
        t=t,
        dt_dz=dt_dz,
        m=m,
        d=d,
        k=k,
    ) + velocity_term("He", grid)
    n_grid["He"] = HE_7 * (T7 / t) * np.exp(-cumulative_trapezoid(y, grid, initial=0.0))

    # *************************************************************************
    # Hydrogen
    # *************************************************************************

    # below 500 km
    mask = (grid >= 150e3) & (grid <= 500e3)
    background = (
        n_grid["N2"][mask]
        + n_grid["O"][mask]
        + n_grid["O2"][mask]
        + n_grid["Ar"][mask]
        + n_grid["He"][mask]
    )
    d = thermal_diffusion_coefficient(
        background,
        t[mask],
        A["H"],
        B["H"],
    )
    alpha = ALPHA["H"]
    _tau = tau_function(z_grid=grid[mask], below_500=True)
    y = (PHI / d) * np.power(t[mask] / T11, 1 + alpha) * np.exp(_tau)  # m^-4
    integral_values = cumulative_trapezoid(
        y[::-1], grid[mask][::-1], initial=0.0
    )  # m^-3
    integral_values = integral_values[::-1]
    n_below_500 = (
        (H_11 - integral_values) * np.power(T11 / t[mask], 1 + alpha) * np.exp(-_tau)
    )

    # above 500 km
    _tau = tau_function(
        z_grid=grid[grid > 500e3],
        below_500=False,
    )
    n_above_500 = H_11 * np.power(T11 / t[grid > 500e3], 1 + alpha) * np.exp(-_tau)

    n_grid["H"] = np.concatenate((n_below_500, n_above_500))

    n = {
        s: log_interp1d(grid, n_grid[s])(altitudes)
        for s in ["N2", "O", "O2", "Ar", "He"]
    }

    # Below 150 km, the number density of atomic hydrogen is zero.
    n_h_below_150 = np.zeros(len(altitudes[altitudes < 150e3]))
    n_h_above_150 = log_interp1d(grid[grid >= 150e3], n_grid["H"])(
        altitudes[altitudes >= 150e3]
    )
    n["H"] = np.concatenate((n_h_below_150, n_h_above_150))

    n_concat: NDArray[np.float64] = np.array([n[species] for species in n])

    return xr.DataArray(
        n_concat,
        dims=["s", "z"],
        coords={
            "s": ("s", [s for s in n]),
            "z": ("z", altitudes, dict(units="m")),
        },
        attrs=dict(units="m^-3"),
    )


def compute_mean_molar_mass_high_altitude(
    z: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute mean molar mass in high-altitude region.

    Parameters
    ----------
    z: array
        Altitude [m].

    Returns
    -------
    array
        Mean molar mass [kg/mole].
    """
    return np.where(z <= 100e3, M0, M["N2"])


def compute_temperature_high_altitude(
    z: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute temperature in high-altitude region.

    Parameters
    ----------
    z: array
        Altitude [m].

    Returns
    -------
    array
        Temperature [K].
    """
    a = -76.3232  # K
    b = -19942.9  # m
    tc = 263.1905  # K

    def t(z: float) -> float:
        """Compute temperature at given altitude.

        Parameters
        ----------
        z: float
            Altitude [m].

        Returns
        -------
        float
            Temperature [K].

        Raises
        ------
        ValueError
            If the altitude is out of range.
        """
        if Z7 <= z <= Z8:
            return T7
        elif Z8 < z <= Z9:
            return tc + a * float(np.sqrt(1.0 - np.power((z - Z8) / b, 2.0)))
        elif Z9 < z <= Z10:
            return T9 + LK9 * (z - Z9)
        elif Z10 < z <= Z12:
            return TINF - (TINF - T10) * float(
                np.exp(-LAMBDA * (z - Z10) * (R0 + Z10) / (R0 + z))
            )
        else:
            raise ValueError(f"altitude value '{z}' is out of range")

    temperature = np.vectorize(t)(z)
    return np.array(temperature, dtype=np.float64)


def compute_temperature_gradient_high_altitude(
    z: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute temperature gradient in high-altitude region.

    Parameters
    ----------
    z: array
        Altitude [m].

    Returns
    -------
    array
        Temperature gradient [K/m].
    """
    a = -76.3232  # [dimensionless]
    b = -19942.9  # m

    def gradient(z_value: float) -> float:
        """Compute temperature gradient at given altitude.

        Parameters
        ----------
        z_value: float
            Altitude [m].

        Raises
        ------
        ValueError
            When altitude is out of bounds.

        Returns
        -------
        float
            Temperature gradient [K / m].
        """
        if Z7 <= z_value <= Z8:
            return LK7
        elif Z8 < z_value <= Z9:
            return (
                -a
                / b
                * ((z_value - Z8) / b)
                / float(np.sqrt(1 - np.square((z_value - Z8) / b)))
            )
        elif Z9 < z_value <= Z10:
            return LK9
        elif Z10 < z_value <= Z12:
            zeta = (z_value - Z10) * (R0 + Z10) / (R0 + z_value)
            return (
                LAMBDA
                * (TINF - T10)
                * float(np.square((R0 + Z10) / (R0 + z_value)))
                * float(np.exp(-LAMBDA * zeta))
            )

        else:
            raise ValueError(
                f"altitude z ({z_value}) out of range, should be in [{Z7}, {Z12}] m"
            )

    z_values: NDArray[np.float64] = np.array(z, dtype=float)
    dt_dz = np.vectorize(gradient)(z_values)
    return np.array(dt_dz, dtype=np.float64)


def thermal_diffusion_coefficient(
    nb: NDArray[np.float64],
    t: NDArray[np.float64],
    a: float,
    b: float,
) -> NDArray[np.float64]:
    r"""Compute thermal diffusion coefficient values in high-altitude region.

    Parameters
    ----------
    nb: array
        Background number density [m^-3].

    t: array
        Temperature [K].

    a: float
        Thermal diffusion constant :math:`a` [m^-1 * s^-1].

    b: float
        Thermal diffusion constant :math:`b` [dimensionless].

    Returns
    -------
    array
        Thermal diffusion coefficient [m^2 * s^-1].
    """
    k = (a / nb) * np.power(t / 273.15, b)
    return np.array(k, dtype=np.float64)


def eddy_diffusion_coefficient(z: NDArray[np.float64]) -> NDArray[np.float64]:
    r"""Compute Eddy diffusion coefficient in high-altitude region.

    Parameters
    ----------
    z: array
        Altitude [m].

    Returns
    -------
    array
        Eddy diffusion coefficient [m^2 * s^-1].

    Notes
    -----
    Valid in the altitude region :math:`86 \leq z \leq 150` km.
    """
    return np.where(
        z < 95e3,
        K_7,
        K_7 * np.exp(1.0 - (4e8 / (4e8 - np.square(z - 95e3)))),
    )


def f_below_115_km(
    g: NDArray[np.float64],
    t: NDArray[np.float64],
    dt_dz: NDArray[np.float64],
    m: Union[float, NDArray[np.float64]],
    mi: float,
    alpha: float,
    d: NDArray[np.float64],
    k: NDArray[np.float64],
) -> NDArray[np.float64]:
    r"""Evaluate function :math:`f` below 115 km altitude.

    Evaluates the function :math:`f` defined by equation (36) in
    :cite:`NASA1976USStandardAtmosphere` in the altitude region :math:`86` km
    :math:`\leq z \leq 115` km.

    Parameters
    ----------
    g: array
        Gravity values at the different altitudes [m * s^-2].

    t: array
        Temperature values at the different altitudes [K].

    dt_dz: array
        Temperature gradient values at the different altitudes [K * m^-1].

    m: array
        Molar mass [kg * mole^-1].

    mi: float
        Species molar masses [kg * mole^-1].

    alpha: float
        Alpha thermal diffusion constant [dimensionless].

    d: array
        Thermal diffusion coefficient values at the different altitudes
        [m^2 * s^-1].

    k: array
        Eddy diffusion coefficient values at the different altitudes
        [m^2 * s^-1].

    Returns
    -------
    array
        Function :math:`f` at the different altitudes.
    """
    term_1 = g * d / ((d + k) * (R * t))
    term_2 = mi + (m * k) / d + (alpha * R * dt_dz) / g
    return term_1 * term_2


def f_above_115_km(
    g: NDArray[np.float64],
    t: NDArray[np.float64],
    dt_dz: NDArray[np.float64],
    mi: float,
    alpha: float,
) -> NDArray[np.float64]:
    r"""Evaluate function :math:`f` above 115 km altitude.

    Evaluate the function :math:`f` defined by equation (36) in
    :cite:`NASA1976USStandardAtmosphere` in the altitude region :math:`115`
    :math:`\lt z \leq 1000` km.

    Parameters
    ----------
    g: array
        Gravity at the different altitudes [m * s^-2].

    t: array
        Temperature at the different altitudes [K].

    dt_dz: array
        Temperature gradient at the different altitudes [K * m^-1].

    mi: float
        Species molar masses [kg * mole^-1].

    alpha: float
        Alpha thermal diffusion constant [dimensionless].

    Returns
    -------
    array
        Function :math:`f` at the different altitudes.
    """
    return (g / (R * t)) * (mi + ((alpha * R) / g) * dt_dz)  # type: ignore


def thermal_diffusion_term(
    s: str,
    z_grid: NDArray[np.float64],
    g: NDArray[np.float64],
    t: NDArray[np.float64],
    dt_dz: NDArray[np.float64],
    m: NDArray[np.float64],
    d: NDArray[np.float64],
    k: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute thermal diffusion term of given species in high-altitude region.

    Parameters
    ----------
    s: str
        Species.

    z_grid: array
        Altitude grid [m].

    g: array
        Gravity values on the altitude grid [m * s^-2].

    t: array
        Temperature values on the altitude grid [K].

    dt_dz: array
        Temperature gradient values on the altitude grid [K * m^-1].

    m: array
        Values of the mean molar mass on the altitude grid [kg * mole^-1].

    d: array
        Molecular diffusion coefficient values on the altitude grid,
        for altitudes strictly less than 115 km [m^2 * s^-1].

    k: array
        Eddy diffusion coefficient values on the altitude grid, for
        altitudes strictly less than 115 km [m^2 * s^-1].

    Returns
    -------
    array
        Thermal diffusion term [m^-1].
    """
    below_115_km = z_grid < 115e3
    fo1 = f_below_115_km(
        g[below_115_km],
        t[below_115_km],
        dt_dz[below_115_km],
        m[below_115_km],
        M[s],
        ALPHA[s],
        d,
        k,
    )
    above_115_km = z_grid >= 115e3
    fo2 = f_above_115_km(
        g[above_115_km],
        t[above_115_km],
        dt_dz[above_115_km],
        M[s],
        ALPHA[s],
    )
    return np.concatenate((fo1, fo2))


def thermal_diffusion_term_atomic_oxygen(
    z_grid: NDArray[np.float64],
    g: NDArray[np.float64],
    t: NDArray[np.float64],
    dt_dz: NDArray[np.float64],
    d: NDArray[np.float64],
    k: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute oxygen thermal diffusion term in high-altitude region.

    Parameters
    ----------
    z_grid: array
        Altitude grid [m].

    g: array
        Gravity values on the altitude grid [m * s^-2].

    t: array
        Temperature values on the altitude grid [K].

    dt_dz: array
        Temperature values gradient on the altitude grid [K * m^-1].

    d: array
        Thermal diffusion coefficient on the altitude grid [m^2 * s^-1].

    k: array
        Eddy diffusion coefficient values on the altitude grid [m^2 * s^-1].

    Returns
    -------
    array
        Thermal diffusion term [-1].
    """
    mask1, mask2 = z_grid < 115e3, z_grid >= 115e3
    x1 = f_below_115_km(
        g=g[mask1],
        t=t[mask1],
        dt_dz=dt_dz[mask1],
        m=M["N2"],
        mi=M["O"],
        alpha=ALPHA["O"],
        d=d,
        k=k,
    )
    x2 = f_above_115_km(
        g=g[mask2],
        t=t[mask2],
        dt_dz=dt_dz[mask2],
        mi=M["O"],
        alpha=ALPHA["O"],
    )
    return np.concatenate((x1, x2))


def velocity_term_hump(
    z: NDArray[np.float64],
    q1: float,
    q2: float,
    u1: float,
    u2: float,
    w1: float,
    w2: float,
) -> NDArray[np.float64]:
    r"""Compute transport term.

    Compute the transport term given by equation (37) in
    :cite:`NASA1976USStandardAtmosphere`.

    Parameters
    ----------
    z: array
        Altitude [m].

    q1: float
        Q constant [m^-3].

    q2: float
        q constant [m^-3].

    u1: float
        U constant [m].

    u2: float
        u constant [m].

    w1: float
        W constant [m^-3].

    w2: float
        w constant [m^-3].

    Returns
    -------
    array:
        Transport term [m^-1].

    Notes
    -----
    Valid in the altitude region: 86 km :math:`\leq z \leq` 150 km.
    """
    t = q1 * np.square(z - u1) * np.exp(-w1 * np.power(z - u1, 3.0)) + q2 * np.square(
        u2 - z
    ) * np.exp(-w2 * np.power(u2 - z, 3.0))
    return np.array(t, dtype=np.float64)


def velocity_term_no_hump(
    z: NDArray[np.float64], q1: float, u1: float, w1: float
) -> NDArray[np.float64]:
    r"""Compute transport term.

    Compute the transport term given by equation (37) in
    :cite:`NASA1976USStandardAtmosphere` where the second term is zero.

    Parameters
    ----------
    z: array
        Altitude.

    q1: float
        Q constant [m^-3].

    u1: float
        U constant [m].

    w1: float
        W constant [m^-3].

    Returns
    -------
    array
        Transport term [m^-1].

    Notes
    -----
    Valid in the altitude region :math:`86` km :math:`\leq z \leq 150` km.
    """
    t = q1 * np.square(z - u1) * np.exp(-w1 * np.power(z - u1, 3.0))  # m^-1
    return np.array(t, np.float64)


def velocity_term(s: str, z_grid: NDArray[np.float64]) -> NDArray[np.float64]:
    """Compute velocity term of a given species in high-altitude region.

    Parameters
    ----------
    s: str
        Species.

    z_grid: array
        Altitude grid [m].

    Returns
    -------
    array
        Velocity term [m^-1].

    Notes
    -----
    Not valid for atomic oxygen. See :func:`velocity_term_atomic_oxygen`.
    """
    x1 = velocity_term_no_hump(
        z=z_grid[z_grid <= 150e3],
        q1=Q1[s],
        u1=U1[s],
        w1=W1[s],
    )

    # Above 150 km, the velocity term is neglected, as indicated at p. 14 in
    # :cite:`NASA1976USStandardAtmosphere`
    x2 = np.zeros(len(z_grid[z_grid > 150e3]))
    return np.concatenate((x1, x2))


def velocity_term_atomic_oxygen(
    grid: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute velocity term of atomic oxygen in high-altitude region.

    Parameters
    ----------
    grid: array
        Altitude grid [m].

    Returns
    -------
    array
        Velocity term [m^-1].
    """
    mask1, mask2 = grid <= 150e3, grid > 150e3
    x1 = np.where(
        grid[mask1] <= 97e3,
        velocity_term_hump(
            z=grid[mask1],
            q1=Q1["O"],
            q2=Q2["O"],
            u1=U1["O"],
            u2=U2["O"],
            w1=W1["O"],
            w2=W2["O"],
        ),  # m^-1
        velocity_term_no_hump(
            z=grid[mask1],
            q1=Q1["O"],
            u1=U1["O"],
            w1=W1["O"],
        ),  # m^-1
    )

    x2 = np.zeros(len(grid[mask2]))
    return np.concatenate((x1, x2))


def tau_function(
    z_grid: NDArray[np.float64], below_500: bool = True
) -> NDArray[np.float64]:
    r"""Compute :math:`\tau` function.

    Compute integral given by equation (40) in
    :cite:`NASA1976USStandardAtmosphere` at each point of an altitude grid.

    Parameters
    ----------
    z_grid: array
        Altitude grid (values sorted by ascending order) to use for integration
        [m].

    below_500: bool, default True
        ``True`` if altitudes in ``z_grid`` are lower than 500 km, False
        otherwise.

    Returns
    -------
    array
        Integral evaluations [dimensionless].

    Notes
    -----
    Valid for 150 km :math:`\leq z \leq` 500 km.
    """
    if below_500:
        z_grid = z_grid[::-1]

    y = (
        M["H"]
        * compute_gravity(z=z_grid)
        / (R * compute_temperature_high_altitude(z=z_grid))
    )  # m^-1
    integral_values: NDArray[np.float64] = np.array(
        cumulative_trapezoid(y, z_grid, initial=0.0), dtype=np.float64
    )

    if below_500:
        values: NDArray[np.float64] = integral_values[::-1]
        return values
    else:
        return integral_values


def log_interp1d(
    x: NDArray[np.float64], y: NDArray[np.float64]
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Compute linear interpolation of :math:`y(x)` in logarithmic space.

    Parameters
    ----------
    x: array
        1-D array of real values.

    y: array
        N-D array of real values. The length of y along the interpolation axis
        must be equal to the length of x.

    Returns
    -------
    callable
        Interpolating function.
    """
    logx = np.log10(x)
    logy = np.log10(y)
    lin_interp = interp1d(logx, logy, kind="linear")

    def log_interp(z: NDArray[np.float64]) -> NDArray[np.float64]:
        value = np.power(10.0, lin_interp(np.log10(z)))
        return np.array(value, dtype=np.float64)

    return log_interp


def compute_pressure_low_altitude(
    h: NDArray[np.float64],
    pb: NDArray[np.float64],
    tb: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute pressure in low-altitude region.

    Parameters
    ----------
    h: array
        Geopotential height [m].

    pb: array
        Levels pressure [Pa].

    tb: array
        Levels temperature [K].

    Returns
    -------
    array
        Pressure [Pa].
    """
    # we create a mask for each layer
    masks = [
        ma.masked_inside(h, H[i - 1], H[i]).mask  # type: ignore
        for i in range(1, len(H))
    ]

    # for each layer, we evaluate the pressure based on whether the
    # temperature gradient is zero or non-zero
    p = np.empty(len(h))
    for i, mask in enumerate(masks):
        if LK[i] == 0:
            p[mask] = compute_pressure_low_altitude_zero_gradient(
                h=h[mask],
                hb=H[i],
                pb=pb[i],
                tb=tb[i],
            )
        else:
            p[mask] = compute_pressure_low_altitude_non_zero_gradient(
                h=h[mask],
                hb=H[i],
                pb=pb[i],
                tb=tb[i],
                lkb=LK[i],
            )
    return p


def compute_pressure_low_altitude_zero_gradient(
    h: Union[float, NDArray[np.float64]],
    hb: float,
    pb: float,
    tb: float,
) -> NDArray[np.float64]:
    """Compute pressure in low-altitude zero temperature gradient region.

    Parameters
    ----------
    h: array
        Geopotential height [m].

    hb: float
        Geopotential height at the bottom of the layer [m].

    pb: float
        Pressure at the bottom of the layer [Pa].

    tb: float
        Temperature at the bottom of the layer [K].

    Returns
    -------
    array
        Pressure [Pa].
    """
    p = pb * np.exp(-G0 * M0 * (h - hb) / (R * tb))
    return np.array(p, dtype=np.float64)


def compute_pressure_low_altitude_non_zero_gradient(
    h: Union[float, NDArray[np.float64]],
    hb: float,
    pb: float,
    tb: float,
    lkb: float,
) -> NDArray[np.float64]:
    """Compute pressure in low-altitude non-zero temperature gradient region.

    Parameters
    ----------
    h: array
        Geopotential height [m].

    hb: float
        Geopotential height at the bottom of the layer [m].

    pb: float
        Pressure at the bottom of the layer [Pa].

    tb: float
        Temperature at the bottom of the layer [K].

    lkb: float
        Temperature gradient in the layer [K * m^-1].

    Returns
    -------
    array
        Pressure [Pa].
    """
    p = pb * np.power(tb / (tb + lkb * (h - hb)), G0 * M0 / (R * lkb))
    return np.array(p, dtype=np.float64)


def compute_temperature_low_altitude(
    h: NDArray[np.float64],
    tb: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute temperature in low-altitude region.

    Parameters
    ----------
    h: array
        Geopotential height [m].

    tb: array
        Levels temperature [K].

    Returns
    -------
    array
        Temperature [K].
    """
    # we create a mask for each layer
    masks = [
        ma.masked_inside(h, H[i - 1], H[i]).mask  # type: ignore
        for i in range(1, len(H))
    ]

    # for each layer, we evaluate the pressure based on whether the
    # temperature gradient is zero or not
    t = np.empty(len(h))
    for i, mask in enumerate(masks):
        if LK[i] == 0:
            t[mask] = tb[i]
        else:
            t[mask] = tb[i] + LK[i] * (h[mask] - H[i])
    return t


def to_altitude(h: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert geopotential height to (geometric) altitude.

    Parameters
    ----------
    h: array
        Geopotential altitude [m].

    Returns
    -------
    array
        Altitude [m].
    """
    return R0 * h / (R0 - h)


def to_geopotential_height(z: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert altitude to geopotential height.

    Parameters
    ----------
    z: array
        Altitude [m].

    Returns
    -------
    array
        Geopotential height [m].
    """
    return R0 * z / (R0 + z)


def compute_gravity(z: NDArray[np.float64]) -> NDArray[np.float64]:
    """Compute gravity.

    Parameters
    ----------
    z : array
        Altitude [m].

    Returns
    -------
    array
        Gravity [m * s^-2].
    """
    return np.array(G0 * np.power((R0 / (R0 + z)), 2.0), dtype=np.float64)
