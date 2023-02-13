"""AFGL 1986 atmosphere's thermophysical profiles.

The profiles are generated from data files stored in ``joseki/data/afgl_1986``.
These data files correspond to tables 1a-f and 2a-d of the technical report
[Anderson+1986](bibliography.md#Anderson+1986).
"""
import enum
import importlib_resources
import logging
import typing as t

import pandas as pd
import pint
import xarray as xr
from attrs import define

from ..units import ureg
from .core import Profile, interp, DEFAULT_METHOD
from .factory import factory
from .schema import history, schema

logger = logging.getLogger(__name__)


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

INSTITUION = "Air Force Geophysics Laboratory"
URL = "https://archive.org/details/DTIC_ADA175173"
URLDATE = "2022-12-12"

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

    Args:
        identifier: Atmospheric profile identifier.

    Returns:
        Atmospheric profile dataset.

    Notes:
        Read the relevant raw data files corresponding to the atmospheric profile.
        These raw data files correspond to tables 1 and 2 from the
        technical report [*AFGL Atmospheric Constituent Profiles (0-120 km)*,
        Anderson et al., 1986](bibliography.md#Anderson+1986).
        Each atmospheric profile has 5 tables, i.e. 5 raw data files, associated
        to it.
        Only the first of these tables is specific to each atmospheric profile.
        All 5 raw data files are read into `pandas.DataFrame` objects and
        then concatenated after dropping the duplicate columns.
    """
    package = "joseki.data.afgl_1986"
    files = DATA_FILES[identifier]
    dataframes = []
    for file in files:
        csvfile = importlib_resources.files(package).joinpath(file)
        df = pd.read_csv(csvfile)
        dataframes.append(df)
    dataframes[1] = dataframes[1].drop(["H2O", "O3", "N2O", "CO", "CH4"], axis=1)
    for i in range(1, 5):
        dataframes[i] = dataframes[i].drop("z", axis=1)

    return pd.concat(dataframes, axis=1)


def dataframe_to_dataset(
    df: pd.DataFrame,
    identifier: Identifier,
    additional_molecules: bool = True,
) -> xr.Dataset:
    """Convert the output of the `parse` method to a `xarray.Dataset`.

    Args:
        df: Atmospheric profile data.
        identifier: Atmospheric profile identifier.
        additional_molecules: If ``True``, include molecules 8-28 as numbered 
            in [Anderson+1986](bibliography.md#Anderson+1986).
            Else, discard molecules 8-28.

    Returns:
        Atmospheric profile dataset.

    Notes:
        Use the ``z`` column of the output pandas.DataFrame of read_raw_data
        as data coordinate and all other columns as data variables.
        All data variables and coordinates of the returned xarray.Dataset are
        associated metadata (standard name, long name and units).
        Raw data units are documented in the technical report *AFGL Atmospheric
        Constituent Profiles (0-120 km)*, Anderson et al., 1986
        [Anderson+1986](bibliography.md#Anderson+1986).
        dataset attributes are added.
    """
    # list molecules
    # molecules labels correspond to column with upper case first letter in
    # raw data DataFrames
    molecules = []
    for column in df.columns:
        if column[0].isupper():
            molecules.append(column)

    if additional_molecules:
        pass
    else:
        molecules = molecules[:7]

    # coordinates
    coords = {"z": ureg.Quantity(df.z.values, "km")}

    # data variables
    data_vars = {}
    data_vars["p"] = ureg.Quantity(df.p.values, "millibar").to("Pa")
    data_vars["t"] = ureg.Quantity(df.t.values, "K")
    data_vars["n"] = ureg.Quantity(df.n.values, "cm^-3").to("m^-3")

    for s in molecules:
        data_vars[f"x_{s}"] = (
            df[s].values * ureg.ppm
        )  # raw data volume fraction are given in ppmv

    # attributes
    pretty_identifier = f"AFGL (1986) {identifier.value.replace('_', '-')}"
    pretty_title = f"{pretty_identifier} atmosphere thernmophysical profile"

    attrs = {
        "Conventions": "CF-1.10",
        "title": pretty_title,
        "institution": INSTITUION,
        "source": SOURCE,
        "history": history(),
        "references": REFERENCE,
        "url": URL,
        "urldate": URLDATE,
    }

    return schema.convert(
        data_vars=data_vars,
        coords=coords,
        attrs=attrs,
    )


def get_dataset(
    identifier: Identifier,
    additional_molecules: bool = True,
) -> xr.Dataset:
    """Read data files for a given atmospheric profile.

    Args:
        identifier: Atmospheric profile identifier.
            See 
            [`Identifier`](reference.md#src.joseki.profiles.afgl_1986.Identifier) 
            for possible values.
        additional_molecules: If ``True``, include molecules 8-28 as numbered in
            [Anderson+1986](bibliography.md#Anderson+1986).
            Else, discard molecules 8-28.

    Returns:
        Atmospheric profile dataset.

    Notes:
        Chain calls to 
        [`parse`](reference.md#src.joseki.profiles.afgl_1986.parse) and
        [`dataframe_to_dataset`](reference.md#src.joseki.profiles.afgl_1986.dataframe_to_dataset).

    """
    df = parse(identifier=identifier)
    return dataframe_to_dataset(
        df=df,
        identifier=identifier,
        additional_molecules=additional_molecules,
    )


def to_dataset(
    identifier: Identifier,
    z: t.Optional[pint.Quantity] = None,
    interp_method: t.Mapping[str, str] = None,
    conserve_column: bool = False,
    **kwargs: t.Any,
) -> xr.Dataset:
    """
    Helper Profile.to_dataset() method.

    Args:
        identifier: AFGL 1986 atmosphere thermophysical profile identifier.
            See 
            [`Identifier`](reference.md#src.joseki.profiles.afgl_1986.Identifier) 
            for possible values.
        z: New level altitudes.
            If ``None``, return the original dataset
            Else, interpolate the dataset to the new level altitudes.
            Default is ``None``.
        interp_method: Interpolation method for each data variable. Default is 
            ``None``.
        conserve_column: If `True`, ensure that column densities are conserved
            during interpolation.
        kwargs: Additional arguments passed to 
            [`get_dataset`](reference.md#src.joseki.profiles.afgl_1986.get_dataset).

    Returns:
        Atmosphere thermophysical profile dataset.
    """
    # Get additional_molecules from kwargs
    additional_molecules = kwargs.get("additional_molecules", True)

    # kwargs different than 'additional_molecules' are ignored
    if len([x for x in kwargs.keys() if x != "additional_molecules"]) > 0:
        logger.warning(
            "Ignoring kwargs different than 'additional_molecules'. "
            "(got %s)"
            "Use 'additional_molecules' to include molecules 8-28 "
            "as numbered in Anderson et al. (1986).",
            kwargs,
        )

    # Get the original dataset
    ds = get_dataset(
        identifier=identifier,
        additional_molecules=additional_molecules,
    )

    # Interpolate if necessary
    if z is not None:
        method = interp_method if interp_method is not None else DEFAULT_METHOD
        ds = interp(
            ds=ds,
            z_new=z,
            method=method,
            conserve_column=conserve_column,
        )
        return ds
    else:
        return ds


@factory.register(identifier="afgl_1986-tropical")
@define
class AFGL1986Tropical(Profile):
    """AFGL 1986 tropical atmosphere thermophysical profile."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        logger.debug(
            "creating AFGL 1986 tropical atmosphere thermophysical profile dataset."
        )
        return to_dataset(
            identifier=Identifier.TROPICAL,
            z=z,
            interp_method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register(identifier="afgl_1986-midlatitude_summer")
@define
class AFGL1986MidlatitudeSummer(Profile):
    """AFGL 1986 midlatitude summer atmosphere thermophysical profile."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        logger.debug(
            "creating AFGL 1986 midlatitude summer atmosphere thermophysical "
            "profile dataset."
        )
        return to_dataset(
            identifier=Identifier.MIDLATITUDE_SUMMER,
            z=z,
            interp_method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register(identifier="afgl_1986-midlatitude_winter")
@define
class AFGL1986MidlatitudeWinter(Profile):
    """AFGL 1986 midlatitude winter atmosphere thermophysical profile."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        logger.debug(
            "creating AFGL 1986 midlatitude winter atmosphere thermophysical "
            "profile dataset."
        )
        return to_dataset(
            identifier=Identifier.MIDLATITUDE_WINTER,
            z=z,
            interp_method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register(identifier="afgl_1986-subarctic_summer")
@define
class AFGL1986SubarcticSummer(Profile):
    """AFGL 1986 subarctic summer atmosphere thermophysical profile."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        logger.debug(
            "creating AFGL 1986 subarctic summer atmosphere thermophysical "
            "profile dataset."
        )
        return to_dataset(
            identifier=Identifier.SUBARCTIC_SUMMER,
            z=z,
            interp_method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register(identifier="afgl_1986-subarctic_winter")
@define
class AFGL1986SubarcticWinter(Profile):
    """AFGL 1986 subarctic winter atmosphere thermophysical profile."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        logger.debug(
            "creating AFGL 1986 subarctic winter atmosphere thermophysical "
            "profile dataset."
        )
        return to_dataset(
            identifier=Identifier.SUBARCTIC_WINTER,
            z=z,
            interp_method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register(identifier="afgl_1986-us_standard")
@define
class AFGL1986USStandard(Profile):
    """AFGL 1986 US Standard atmosphere thermophysical profile."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        logger.debug(
            "creating AFGL 1986 US Standard atmosphere thermophysical profile dataset."
        )
        return to_dataset(
            identifier=Identifier.US_STANDARD,
            z=z,
            interp_method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )
