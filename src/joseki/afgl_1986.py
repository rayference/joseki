"""Module to read AFGL 1986 data files."""
import importlib.resources as pkg_resources

import numpy as np
import pandas as pd
import xarray as xr

from .data import afgl_1986
from joseki import core
from joseki import ureg

TABLE_2_DATA_FILES = (
    "table_2a.csv",
    "table_2b.csv",
    "table_2c.csv",
    "table_2d.csv",
)
DATA_FILES = {
    "afgl_1986-tropical": ("table_1a.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-midlatitude_summer": ("table_1b.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-midlatitude_winter": ("table_1c.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-subarctic_summer": ("table_1d.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-subarctic_winter": ("table_1e.csv", *TABLE_2_DATA_FILES),
    "afgl_1986-us_standard": ("table_1f.csv", *TABLE_2_DATA_FILES),
}


def read_raw_data(identifier: str) -> pd.DataFrame:
    """Read the raw data files for a given atmospheric profile identifier.

    Read the relevant raw data files corresponding to the atmospheric profile
    identifier. These raw data files correspond to tables 1 and 2 from the
    technical report *AFGL Atmospheric Constituent Profiles (0-120 km)*,
    Anderson et al., 1986
    :cite:`Anderson1986AtmosphericConstituentProfiles`.
    Each atmospheric profile has 5 tables, i.e. 5 raw
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
        ``"afgl_1986-us_standard"``].

    Returns
    -------
    :class:`~pandas.DataFrame`
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
        with pkg_resources.path(afgl_1986, file) as path:
            dataframes.append(pd.read_csv(path))
    dataframes[1] = dataframes[1].drop(["H2O", "O3", "N2O", "CO", "CH4"], axis=1)
    for i in range(1, 5):
        dataframes[i] = dataframes[i].drop("z", axis=1)

    return pd.concat(dataframes, axis=1)


def to_xarray(raw_data: pd.DataFrame) -> xr.Dataset:
    """Convert :meth:`read_raw_data`'s output to a :class:`~xarray.Dataset`.

    Use the ``z`` column of the output pandas.DataFrame of read_raw_data
    as data coordinate and all other columns as data variables.
    All data variables and coordinates of the returned xarray.Dataset are
    associated metadata (standard name, long name and units).
    Raw data units are documented in the technical report *AFGL Atmospheric
    Constituent Profiles (0-120 km)*, Anderson et al., 1986
    :cite:`Anderson1986AtmosphericConstituentProfiles`.
    Data set attributes are added.

    Parameters
    ----------
    raw_data: :class:`~pandas.DataFrame`
        Raw atmospheric profile data.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile data set.
    """
    # list species
    # species labels correspond to column with upper case first letter in
    # raw data DataFrames
    species = []
    for column in raw_data.columns:
        if column[0].isupper():
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

    ds: xr.Dataset = core.make_data_set(
        p=p, t=t, n=n, mr=mr, z_level=z_level, species=np.array(species)
    )
    return ds


def read_raw_data_to_xarray(identifier: str) -> xr.Dataset:
    """Chain calls to :meth:`read_raw_data` and :meth:`to_xarray`.

    Parameters
    ----------
    identifier: str
        Atmospheric profile identifier in [``"afgl_1986-tropical"``,
        ``"afgl_1986-midlatitude_summer"``, ``"afgl_1986-midlatitude_winter"``,
        ``"afgl_1986-subarctic_summer"``, ``"afgl_1986-subarctic_winter"``,
        ``"afgl_1986-us_standard"``].

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile data set.
    """
    df = read_raw_data(identifier=identifier)
    return to_xarray(df)
