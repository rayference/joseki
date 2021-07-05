"""Module to read AFGL 1986 data files."""
import importlib.resources as pkg_resources

import numpy as np
import pandas as pd
import xarray as xr

from .data import afgl_1986
from joseki import ureg
from joseki import util

SOURCE = (
    "Atmospheric model (U.S. Standard Atmosphere) adapted from "
    "satellite data and/or dynamical-photochemical analyses."
)

REFERENCE = (
    "Anderson, G.P. and Chetwynd J.H. and Clough S.A. and "
    "Shettle E.P. and Kneizys F.X., AFGL Atmospheric "
    "Constituent Profiles (0-120km), 1986, Air Force "
    "Geophysics Laboratory, AFGL-TR-86-0110, "
    "https://ui.adsabs.harvard.edu/abs/1986afgl.rept.....A/abstract"
)

TABLE_2_DATA_FILES = (
    "table_2a.csv",
    "table_2b.csv",
    "table_2c.csv",
    "table_2d.csv",
)

DATA_FILES = {
    "tropical": ("table_1a.csv", *TABLE_2_DATA_FILES),
    "midlatitude_summer": ("table_1b.csv", *TABLE_2_DATA_FILES),
    "midlatitude_winter": ("table_1c.csv", *TABLE_2_DATA_FILES),
    "subarctic_summer": ("table_1d.csv", *TABLE_2_DATA_FILES),
    "subarctic_winter": ("table_1e.csv", *TABLE_2_DATA_FILES),
    "us_standard": ("table_1f.csv", *TABLE_2_DATA_FILES),
}


def parse(name: str) -> pd.DataFrame:
    """Parse table data files for a given atmospheric profile.

    Read the relevant raw data files corresponding to the atmospheric profile.
    These raw data files correspond to tables 1 and 2 from the
    technical report *AFGL Atmospheric Constituent Profiles (0-120 km)*,
    Anderson et al., 1986
    :cite:`Anderson1986AtmosphericConstituentProfiles`.
    Each atmospheric profile has 5 tables, i.e. 5 raw data files, associated
    to it.
    Only the first of these tables is specific to each atmospheric profile.
    All 5 raw data files are read into :class:`~pandas.DataFrame` objects and
    then concatenated after dropping the duplicate columns.

    Parameters
    ----------
    name: str
        Atmospheric profile name in [``"tropical"``,
        ``"midlatitude_summer"``, ``"midlatitude_winter"``,
        ``"subarctic_summer"``, ``"subarctic_winter"``,
        ``"us_standard"``].

    Returns
    -------
    :class:`~pandas.DataFrame`
        Atmospheric profile data set.

    Raises
    ------
    ValueError
        If ``name`` is invalid.
    """
    try:
        files = DATA_FILES[name]
    except KeyError:
        raise ValueError(
            f"'name' must be either 'tropical', "
            f"'midlatitude_summer', 'midlatitude_winter', "
            f"'subarctic_summer', 'subarctic_winter', "
            f"or 'us_standard' (got {name})"
        )
    dataframes = []
    for file in files:
        with pkg_resources.path(afgl_1986, file) as path:
            dataframes.append(pd.read_csv(path))
    dataframes[1] = dataframes[1].drop(["H2O", "O3", "N2O", "CO", "CH4"], axis=1)
    for i in range(1, 5):
        dataframes[i] = dataframes[i].drop("z", axis=1)

    return pd.concat(dataframes, axis=1)


def to_xarray(df: pd.DataFrame, name: str, **kwargs: str) -> xr.Dataset:
    """Convert :meth:`parse`'s output to a :class:`~xarray.Dataset`.

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
    df: :class:`~pandas.DataFrame`
        Atmospheric profile data.

    name: str
        Atmospheric profile name in [``"tropical"``,
        ``"midlatitude_summer"``, ``"midlatitude_winter"``,
        ``"subarctic_summer"``, ``"subarctic_winter"``,
        ``"us_standard"``].

    kwargs: str
        Additional arguments passed to :meth:`util.make_data_set`.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile data set.
    """
    # list species
    # species labels correspond to column with upper case first letter in
    # raw data DataFrames
    species = []
    for column in df.columns:
        if column[0].isupper():
            species.append(column)

    # level altitudes
    z = ureg.Quantity(df.z.values, "km")

    # air pressures
    p = ureg.Quantity(df.p.values, "millibar").to("Pa")

    # air temperatures
    t = ureg.Quantity(df.t.values, "K")

    # air number density
    n = ureg.Quantity(df.n.values, "cm^-3").to("m^-3")

    # mixing ratios
    mr_values = []
    for s in species:
        mrs = df[s].values * 1e-6  # raw data mixing ratios are in ppmv
        mr_values.append(mrs)
    mr = ureg.Quantity(np.array(mr_values), "")

    ds: xr.Dataset = util.make_data_set(
        p=p,
        t=t,
        n=n,
        mr=mr,
        z=z,
        species=np.array(species),
        title=f"AFGL (1986) {name.replace('_', '-')} atmospheric profile",
        source=SOURCE,
        references=REFERENCE,
        **kwargs,
    )
    return ds


def read(name: str) -> xr.Dataset:
    """Read data files for a given atmospheric profile.

    Chain calls to :meth:`parse` and :meth:`to_xarray`.

    Parameters
    ----------
    name: str
        Atmospheric profile name in [``"tropical"``,
        ``"midlatitude_summer"``, ``"midlatitude_winter"``,
        ``"subarctic_summer"``, ``"subarctic_winter"``,
        ``"us_standard"``].

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile data set.
    """
    df = parse(name=name)
    return to_xarray(
        df=df,
        name=name,
        func_name="joseki.afgl_1986.read",
        operation="data set creation",
    )
