"""Module to read AFGL 1986 data files."""
import enum
import importlib.resources as pkg_resources

import numpy as np
import pandas as pd
import xarray as xr

from .data import afgl_1986
from .units import ureg
from .util import make_data_set


class Identifier(enum.Enum):
    """AFGL 1986 atmospheric profile identifier enumeration."""

    TROPICAL = "tropical"
    MIDLATITUDE_SUMMER = "midlatitude_summer"
    MIDLATITUDE_WINTER = "midlatitude_winter"
    SUBARCTIC_SUMMER = "subarctic_summer"
    SUBARCTIC_WINTER = "subarctic_winter"
    US_STANDARD = "us_standard"


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
    Identifier.TROPICAL: ("table_1a.csv", *TABLE_2_DATA_FILES),
    Identifier.MIDLATITUDE_SUMMER: ("table_1b.csv", *TABLE_2_DATA_FILES),
    Identifier.MIDLATITUDE_WINTER: ("table_1c.csv", *TABLE_2_DATA_FILES),
    Identifier.SUBARCTIC_SUMMER: ("table_1d.csv", *TABLE_2_DATA_FILES),
    Identifier.SUBARCTIC_WINTER: ("table_1e.csv", *TABLE_2_DATA_FILES),
    Identifier.US_STANDARD: ("table_1f.csv", *TABLE_2_DATA_FILES),
}


def parse(identifier: Identifier) -> pd.DataFrame:
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
    identifier: Identifier
        Atmospheric profile identifier.

    Returns
    -------
    :class:`~pandas.DataFrame`
        Atmospheric profile data set.
    """
    files = DATA_FILES[identifier]
    dataframes = []
    for file in files:
        with pkg_resources.path(afgl_1986, file) as path:
            dataframes.append(pd.read_csv(path))
    dataframes[1] = dataframes[1].drop(["H2O", "O3", "N2O", "CO", "CH4"], axis=1)
    for i in range(1, 5):
        dataframes[i] = dataframes[i].drop("z", axis=1)

    return pd.concat(dataframes, axis=1)


def to_xarray(
    df: pd.DataFrame,
    identifier: Identifier,
    additional_molecules: bool = True,
    **kwargs: str,
) -> xr.Dataset:
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

    identifier: Identifier
        Atmospheric profile identifier.

    additional_molecules: bool
        If ``True``, include molecules 8-28 as numbered in
        :cite:`Anderson1986AtmosphericConstituentProfiles`.
        Else, discard molecules 8-28.

    kwargs: str
        Additional arguments passed to :meth:`util.make_data_set`.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile data set.
    """
    # list molecules
    # molecules labels correspond to column with upper case first letter in
    # raw data DataFrames
    molecules = []
    for column in df.columns:
        if column[0].isupper():
            molecules.append(column)

    # level altitudes
    z = ureg.Quantity(df.z.values, "km")

    # air pressures
    p = ureg.Quantity(df.p.values, "millibar").to("Pa")

    # air temperatures
    t = ureg.Quantity(df.t.values, "K")

    # air number density
    n = ureg.Quantity(df.n.values, "cm^-3").to("m^-3")

    # mixing ratios
    x_values = []
    for s in molecules:
        xs = df[s].values * 1e-6  # raw data mixing ratios are in ppmv
        x_values.append(xs)
    x = ureg.Quantity(np.array(x_values), "")

    ds: xr.Dataset = make_data_set(
        p=p,
        t=t,
        n=n,
        x=x,
        z=z,
        molecules=np.array(molecules),
        title=f"AFGL (1986) {identifier.value.replace('_', '-')} atmospheric profile",
        source=SOURCE,
        references=REFERENCE,
        **kwargs,
    )
    if additional_molecules:
        return ds
    else:
        return ds.isel(molecules=range(1, 8))


def read(identifier: Identifier, additional_molecules: bool = True) -> xr.Dataset:
    """Read data files for a given atmospheric profile.

    Chain calls to :meth:`parse` and :meth:`to_xarray`.

    Parameters
    ----------
    identifier: Identifier
        Atmospheric profile identifier.
        See :class:`.Identifier` for possible values.

    additional_molecules: bool
        If ``True``, include molecules 8-28 as numbered in
        :cite:`Anderson1986AtmosphericConstituentProfiles`.
        Else, discard molecules 8-28.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile data set.
    """
    df = parse(identifier=identifier)
    return to_xarray(
        df=df,
        identifier=identifier,
        additional_molecules=additional_molecules,
        func_name="joseki.afgl_1986.read",
        operation="data set creation",
    )
