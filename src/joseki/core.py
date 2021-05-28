"""Core module."""
import importlib.resources as pkg_resources

import pandas as pd

from . import data

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
    pandas.DataFrame
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
