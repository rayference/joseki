"""Core module."""
import datetime
import importlib.resources as pkg_resources
import pathlib
from typing import Optional
from typing import Union

import numpy as np
import pandas as pd
import pint
import xarray as xr
from scipy import interpolate

from .data import afgl_1986
from .util import add_comment
from .util import to_quantity
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


@ureg.wraps(ret=None, args=("Pa", "K", "m^-3", "", "km", ""), strict=False)
def make_data_set(
    p: Union[pint.Quantity, np.ndarray],
    t: Union[pint.Quantity, np.ndarray],
    n: Union[pint.Quantity, np.ndarray],
    mr: Union[pint.Quantity, np.ndarray],
    z_level: Union[pint.Quantity, np.ndarray],
    species: Union[pint.Quantity, np.ndarray],
) -> xr.Dataset:
    """Make an atmospheric profile data set.

    Parameters
    ----------
    p: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Pressure [Pa].

    t: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Temperature [K].

    n: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Number density [m^-3].

    mr: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Volume mixing ratios [/].

    z_level: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Level altitude [km].

    species: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Species [/].

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    return xr.Dataset(
        data_vars=dict(
            p=(
                "z_level",
                p,
                dict(
                    standard_name="air_pressure",
                    long_name="air pressure",
                    units="Pa",
                ),
            ),
            t=(
                "z_level",
                t,
                dict(
                    standard_name="air_temperature",
                    long_name="air temperature",
                    units="K",
                ),
            ),
            n=(
                "z_level",
                n,
                dict(
                    standard_name="air_number_density",
                    long_name="air number density",
                    units="m^-3",
                ),
            ),
            mr=(
                ("species", "z_level"),
                mr,
                dict(
                    standard_name="mixing_ratio",
                    long_name="mixing ratio",
                    units="",
                ),
            ),
        ),
        coords=dict(
            z_level=(
                "z_level",
                z_level,
                dict(
                    standard_name="level_altitude",
                    long_name="level altitude",
                    units="km",
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
                "- data set creation - joseki.core.make_data_set"
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

    ds: xr.Dataset = make_data_set(
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


@ureg.wraps(ret=None, args=(None, "km", None, None, None, None), strict=False)
def interp(
    ds: xr.Dataset,
    z_level_new: Union[pint.Quantity, np.ndarray],
    p_interp_method: str = "linear",
    t_interp_method: str = "linear",
    n_interp_method: str = "linear",
    x_interp_method: str = "linear",
) -> xr.Dataset:
    """Interpolate atmospheric profile on new level altitudes.

    Parameters
    ----------
    ds: :class:`~xarray.Dataset`
        Atmospheric profile to interpolate.

    z_level_new: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Level altitudes to interpolate the atmospheric profile at [km].

    p_interp_method: str
        Pressure interpolation method.

    t_interp_method: str
        Temperature interpolation method.

    n_interp_method: str
        Number density interpolation method.

    x_interp_method: str
        Volume mixing ratio interpolation method.

    Returns
    -------
    :class:`~xarray.Dataset`
        Interpolated atmospheric profile.
    """
    # Interpolate pressure
    fp = interpolate.interp1d(
        ds.z_level.values, ds.p.values, kind=p_interp_method, bounds_error=True
    )
    p_new = fp(z_level_new)

    # Interpolate temperature
    ft = interpolate.interp1d(
        ds.z_level.values, ds.t.values, kind=t_interp_method, bounds_error=True
    )
    t_new = ft(z_level_new)

    # Interpolate number density
    fn = interpolate.interp1d(
        ds.z_level.values, ds.n.values, kind=n_interp_method, bounds_error=True
    )
    n_new = fn(z_level_new)

    # Interpolate volume mixing ratio
    mr_new = ds.mr.interp(
        z_level=z_level_new, method=x_interp_method, kwargs=dict(bounds_error=True)
    )

    # Reform data set
    interpolated: xr.Dataset = make_data_set(
        p=p_new,
        t=t_new,
        n=n_new,
        mr=mr_new.values,
        z_level=z_level_new,
        species=ds.species.values,
    )

    add_comment(
        ds=interpolated,
        comment=(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            "- data set interpolation - joseki.core.interp"
        ),
    )
    return interpolated


def set_main_coord_to_layer_altitude(
    ds: xr.Dataset,
    p_interp_method: str = "linear",
    t_interp_method: str = "linear",
    n_interp_method: str = "linear",
    x_interp_method: str = "linear",
) -> xr.Dataset:
    """Set the main coordinate to the layer altitude.

    For an atmospheric profile with level altitude as the main coordinate,
    compute the corresponding layer altitude mesh and interpolate the
    data variables onto that layer altitude mesh. The level altitude coordinate
    is preserved but is not a dimension coordinate anymore.

    Parameters
    ----------
    ds: :class:`~xarray.Dataset`
        Atmospheric profile with level altitude as main coordinate.

    p_interp_method: str
        Pressure interpolation method.

    t_interp_method: str
        Temperature interpolation method.

    n_interp_method: str
        Number density interpolation method.

    x_interp_method: str
        Volume mixing ratio interpolation method.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile with layer altitude as main coordinate.
    """
    # Compute layer altitudes
    z_level = to_quantity(ds.z_level)
    z_layer = (z_level[:-1] + z_level[1:]) / 2.0

    # Interpolate at the layer altitudes (z_layer)
    interpolated: xr.Dataset = interp(
        ds=ds,
        z_level_new=z_layer,
        p_interp_method=p_interp_method,
        t_interp_method=t_interp_method,
        n_interp_method=n_interp_method,
        x_interp_method=x_interp_method,
    )

    # Rename z_level into z_layer
    interpolated = interpolated.rename({"z_level": "z_layer"})

    # Add attributes to z_layer coordinate
    interpolated.z_layer.attrs = dict(
        standard_name="layer_altitude",
        long_name="layer altitude",
        units="km",
    )

    # Re-insert z_level (non-dimension) coordinate
    interpolated.coords["z_level"] = (
        "z_levelc",
        z_level,
        dict(
            standard_name="level_altitude",
            long_name="level altitude",
            units="km",
        ),
    )

    # Update metadata
    add_comment(
        ds=interpolated,
        comment=(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            "- data set coords update - joseki.core.set_main_coord_to_layer_altitude"
        ),
    )

    return interpolated


def make(
    identifier: str,
    level_altitudes: Optional[pathlib.Path] = None,
    main_coord_to_layer_altitude: bool = False,
    p_interp_method: str = "linear",
    t_interp_method: str = "linear",
    n_interp_method: str = "linear",
    x_interp_method: str = "linear",
) -> xr.Dataset:
    """Make atmospheric profile data set.

    This method creates an atmospheric profile data set corresponding to the
    specified identifier.
    It allows to interpolate the atmospheric profile on a different
    level altitude mesh as well as to set the layer altitude as the data
    set's main coordinate.

    Parameters
    ----------
    identifier: str
        Atmospheric profile identifier.

    level_altitudes: pathlib.Path
        Level altitudes data file.
        If ``None``, the original atmospheric profile level altitudes are used.

    main_coord_to_layer_altitude: bool
        If ``True``, set the layer altitude as the data set's main coordinate.

    p_interp_method: str
        Pressure interpolation method.

    t_interp_method: str
        Temperature interpolation method.

    n_interp_method: str
        Number density interpolation method.

    x_interp_method: str
        Volume mixing ratios interpolation method

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    ds = read_raw_data_to_xarray(identifier=identifier)

    if level_altitudes is not None:
        z_level = np.loadtxt(fname=level_altitudes, dtype=float, comments="#")
        ds = interp(
            ds=ds,
            z_level_new=z_level,
            p_interp_method=p_interp_method,
            t_interp_method=t_interp_method,
            n_interp_method=n_interp_method,
            x_interp_method=x_interp_method,
        )

    if main_coord_to_layer_altitude:
        ds = set_main_coord_to_layer_altitude(
            ds=ds,
            p_interp_method=p_interp_method,
            t_interp_method=t_interp_method,
            n_interp_method=n_interp_method,
            x_interp_method=x_interp_method,
        )

    return ds
