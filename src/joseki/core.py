"""Core module."""
import datetime
import importlib.resources as pkg_resources
from typing import Union

import numpy as np
import pandas as pd
import pint
import xarray as xr

from . import data

ureg = pint.UnitRegistry()

TABLE_2_DATA_FILES = (
    "afgl_1986-table_2a.csv",
    "afgl_1986-table_2b.csv",
    "afgl_1986-table_2c.csv",
    "afgl_1986-table_2d.csv",
)
DATA_FILES = {
    "afgl_1986-tropical": ("afgl_1986-table_1a.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-midlatitude_summer": ("afgl_1986-table_1b.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-midlatitude_winter": ("afgl_1986-table_1c.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-subarctic_summer": ("afgl_1986-table_1d.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-subarctic_winter": ("afgl_1986-table_1e.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-us_standard": ("afgl_1986-table_1f.csv", *TABLE_2_DATA_FILES),
}


def read_raw_data(identifier: str) -> pd.DataFrame:
    """Read the raw data files for a given atmospheric profile identifier.

    Read the relevant raw data files corresponding to the atmospheric profile
    identifier. These raw data files correspond to tables 1 and 2 from the
    technical report *AFGL Atmospheric Constituent Profiles (0-120 km)*,
    Anderson et al., 1986. Each atmospheric profile has 5 tables, i.e. 5 raw
    data files, associated to it. Only the first of these tables is specific
    to each atmospheric profile. All 5 raw data files are read into
    pandas.DataFrame objects and then concatenated after dropping the
    duplicate columns. The final concatenated pandas.DataFrame object
    has the following columns:

    * ``z``: level altitude [km]
    * ``p``: air pressure [mb]
    * ``t``: air temperature [K]
    * ``n``: air number density [cm^-3]
    * ``X``: ``X``'s mixing ratio [ppmv]

    where ``X`` denotes one of the following 28 molecule species: H2O, CO2, O3,
    N2O, CO, CH4, O2, NO, SO2, NO2, NH3, HNO3, OH, HF, HCl, HBr, HI, ClO, OCS,
    H2CO, HOCl, N2, HCN, CH3Cl, H2O2, C2H2, C2H6 and PH3.

    Parameters
    ----------
    identifier: str
        Atmospheric profile identifier in [``"afgl_1986-tropical"``,
        ``"afgl_1986-midlatitude_summer"``, ``"afgl_1986-midlatitude_winter"``,
        ``"afgl_1986-subarctic_summer"``, ``"afgl_1986-subarctic_winter"``,
        ``"afgl_1986-us_standard"``]

    Returns
    -------
    :class:`pandas.DataFrame`
        Raw atmospheric profile data.

    Raises
    ------
    ValueError
        If ``identifier`` is invalid.
    """
    try:
        files = DATA_FILES[identifier]
    except KeyError:
        raise ValueError(
            f"identifier must be either 'afgl_1986-tropical', "
            f"'afgl_1986-midlatitude_summer', 'afgl_1986-midlatitude_winter', "
            f"'afgl_1986-subarctic_summer', 'afgl_1986-subarctic_winter', "
            f"or 'afgl_1986-us_standard' (got {identifier})"
        )
    dataframes = []
    for file in files:
        with pkg_resources.path(data, file) as path:
            dataframes.append(pd.read_csv(path))
    dataframes[1] = dataframes[1].drop(["H2O", "O3", "N2O", "CO", "CH4"], axis=1)
    for i in range(1, 5):
        dataframes[i] = dataframes[i].drop("z", axis=1)

    return pd.concat(dataframes, axis=1)


def to_xarray(raw_data: pd.DataFrame) -> xr.Dataset:
    """Convert the output of read_raw_data to a xarray.Dataset.

    Use the ``z`` column of the output pandas.DataFrame of read_raw_data
    as data coordinate and all other columns as data variables.
    All data variables and coordinates of the returned xarray.Dataset are
    associated metadata (standard name, long name and units).
    Raw data units are documented in the technical report *AFGL Atmospheric
    Constituent Profiles (0-120 km)*, Anderson et al., 1986.
    Data set attributes are added.

    Parameters
    ----------
    raw_data: :class:`pandas.DataFrame`
        Raw atmospheric profile data.

    Returns
    -------
    :class:`xarray.Dataset`
        Atmospheric profile data set.
    """
    # list species
    # species labels correspond to upper case columns in raw data DataFrames
    species = []
    for column in raw_data.columns:
        if column.isupper():
            species.append(column)
    # level altitudes
    z_level = ureg.Quantity(raw_data.z.values, "km")
    # air pressures
    p = ureg.Quantity(raw_data.p.values, "millibar").to("Pa")
    # air temperatures
    t = ureg.Quantity(raw_data.t.values, "K")
    # air number density
    n = ureg.Quantity(raw_data.n.values, "cm^-3").to("m^-3")
    # mixing ratios
    mr_values = []
    for s in species:
        mrs = raw_data[s].values * 1e-6  # raw data mixing ratios are in ppmv
        mr_values.append(mrs)
    mr = ureg.Quantity(np.array(mr_values), "")

    return xr.Dataset(
        data_vars=dict(
            p=(
                "z_level",
                p.magnitude,
                dict(
                    standard_name="air_pressure",
                    long_name="air pressure",
                    units=p.units,
                ),
            ),
            t=(
                "z_level",
                t.magnitude,
                dict(
                    standard_name="air_temperature",
                    long_name="air temperature",
                    units=t.units,
                ),
            ),
            n=(
                "z_level",
                n.magnitude,
                dict(
                    standard_name="air_number_density",
                    long_name="air number density",
                    units=n.units,
                ),
            ),
            mr=(
                ("species", "z_level"),
                mr.magnitude,
                dict(
                    standard_name="mixing_ratio",
                    long_name="mixing ratio",
                    units=mr.units,
                ),
            ),
        ),
        coords=dict(
            z_level=(
                "z_level",
                z_level.magnitude,
                dict(
                    standard_name="level_altitude",
                    long_name="level altitude",
                    units=z_level.units,
                ),
            ),
            species=(
                "species",
                species,
                dict(
                    standard_name="species",
                    long_name="species",
                    units="",
                ),
            ),
        ),
        attrs=dict(
            convention="CF-1.8",
            title="Atmospheric thermophysical properties profile",
            history=(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                "- data set creation - joseki"
            ),
            source=(
                "Atmospheric model (U.S. Standard Atmosphere) adapted from "
                "satellite data and/or dynamical-photochemical analyses."
            ),
            references=(
                "Anderson, G.P. and Chetwynd J.H. and Clough S.A. and "
                "Shettle E.P. and Kneizys F.X., AFGL Atmospheric "
                "Constituent Profiles (0-120km), 1986, Air Force "
                "Geophysics Laboratory, AFGL-TR-86-0110, "
                "https://ui.adsabs.harvard.edu/abs/1986afgl.rept.....A/abstract"
            ),
        ),
    )


@ureg.wraps(ret=None, args=(None, "km"), strict=False)
def interp(ds: xr.Dataset, z_level: Union[pint.Quantity, np.ndarray]) -> xr.Dataset:
    """Interpolate atmospheric profile.

    Parameters
    ----------
    ds: :class:`xarray.Dataset`
        Atmospheric profile to interpolate.

    z_level: :class:`pint.Quantity`, :class:`numpy.ndarray`
        Level altitudes to interpolate the atmospheric profile at [km].

    Returns
    -------
    :class:`xarray.Dataset`
        Interpolated atmospheric profile.
    """
    return ds.interp(z_level=z_level, kwargs=dict(bounds_error=True))
