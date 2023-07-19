"""Utilities to create a profile from 
[reanalysis datasets](https://confluence.ecmwf.int/display/CKB/CAMS%3A+Reanalysis+data+documentation)
([Inness+2019](bibliography.md#Inness+2019)) as provided by the
Copernicus Atmospheric Monitoring Service (CAMS).
"""
from __future__ import annotations

import datetime
import importlib_resources
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from os import PathLike

import numpy as np
import pandas as pd
import pint
import xarray as xr

from ..units import ureg, to_quantity
from .util import mass_fraction_to_mole_fraction3, to_m_suffixed_data
from .schema import schema
from .core import DEFAULT_METHOD
from .core import regularize as _regularize, extrapolate as _extrapolate

logger = logging.getLogger(__name__)

# TODO: complete this mapping
# Mapping of CAMS specific ratio data variables names to molecule formula.
MOLECULE = {
    "co": "CO",
    "q": "H2O",
    "go3": "O3",
    "hno3": "HNO3",
    "no2": "NO2",
    "no": "NO",
    "oh": "OH",
    "o3": "O3",
    "so2": "SO2",
    "ch4": "CH4",
    "co2": "CO2",
}

# TODO: complete this mapping
# Mapping of total amounts variable names to molecule formula.
MOLECULE_TOTALS = {
    "tcco": "CO",
    "tc_ch4": "CH4",
    "tcno2": "NO2",
    "tc_no": "NO",
    "gtco3": "O3",
    "tcso2": "SO2",
    "tcwv": "H2O",
    "tcch4": "CH4",
    "tcco2": "CO2",
}


def from_cams_reanalysis(
    data: PathLike | list[PathLike],
    identifier: str,
    time: str | datetime.datetime | np.datetime64,
    lat: float | pint.Quantity,
    lon: float | pint.Quantity,
    molecules: list[str] | None = None,
    missing_molecules_from: xr.Dataset | None = None,
    extrapolate: dict | None = None,
    regularize: bool | dict | None = None,
    extract_dir : Path | None = None,
    pressure_data : str | None = "surface_pressure",
) -> xr.Dataset:
    """Convert CAMS reanalysis data to a profile.

    Args:
        data: Path to CAMS data archive file or list of paths to CAMS datasets 
            or path to directory where CAMS datasets are located.
        identifier: `'EAC4'` for a *CAMS reanalysis of atmospheric composition* 
            dataset, `'EGG4'` for a *CAMS global greenhouse gas reanalysis*
            dataset. This is used to populate the dataset `reference`, `url` 
            and `urldate` attributes.
        time: Time.
        lat: Latitude [degrees].
        lon: Longitude [degrees].
        molecules: List of molecules to include in the profile. If this list
            includes molecules that are not in the CAMS data.
            If None, all molecules are included.
        missing_molecules_from: Reference dataset to use for missing molecules.
        extrapolate: Specifications to extrapolate the CAMS data to lower/upper 
            altitudes. Accepted keys: 'up', 'down' and 'method'. 
            For each key in ['up', down'], the value is another mapping with
            a required 'z' key that specifies the altitude values to extrapolate
            to and an optional 'method' key that is a dictionary that maps 
            data variables and extrapolation methods to use.
        regularize: Specifications to regularize the altitude grid.
            'method': Data variable and interpolation method mapping. When the
                interpolation method is not specified for a data variable, the
                default method is used.
            'conserve_column': If True, ensure that column densities are 
                conserved.
            'options': Regularization options.
        extract_dir: Directory where to extract the CAMS data. If None, a
            temporary directory is used.
        pressure_data: indicates how to compute the pressure data. Either
            'model_level_60' or 'surface_pressure'. If 'model_level_60',
            the pressure data is computed from the L60 model level table.
            If 'surface_pressure', the pressure data is computed by rescaling
            the L60 model level table with the surface pressure from the CAMS
            surface dataset.
    
    Raises:
        ValueError: If the dataset is not a multi-level dataset or if the 
            archive does not contain a multi-level dataset.
        ValueError: If molecules are requested that are not in the dataset
            and `missing_molecules_from` is not specified.
        ValueError: If `pressure_data` is set to `'surface_pressure'` but the
            CAMS surface dataset is not provided.

    Returns:
        Profile dataset.

    Notes:
        Supports only the 
        [CAMS reanalysis datasets](https://confluence.ecmwf.int/display/CKB/CAMS%3A+Reanalysis+data+documentation).
        Furthermore, the dataset must be a multi-level dataset, (identified as 
        such with the presence of a 'level' coordinate).

        There are currently some assumptions/limitations with respect to the 
        conversion of CAMS 'model levels' into altitude values:
        * The model level to altitude conversion is based on the 
          [L60 model level definitions](https://confluence.ecmwf.int/display/UDOC/L60+model+level+definitions)
          where the "n" and "Geometric Altitude [m]" table columns provide
          the relationship between model levels and altitude values.
        * This conversion thus assumes that the local ground surface is at
          mean sea level, as in the U.S. Standard Atmosphere, 1976 model.
          This means that significant deviations occur when the local ground
          surface is not at mean sea level.
        * The CAMS data does not provide the air pressure on model levels.
          The pressure data injected in the profile build here is also based
          on the *L60 model level table*, i.e. the U.S. Standard Atmosphere, 
          1976 model. This means that the pressure profile is always the same.
    """
    longitude = to_quantity(lon, units="degree")
    latitude = to_quantity(lat, units="degree")

    # Open datasets (we sort by time because CAMS data is not always sorted by 
    # time and this is required to select at a timestamp)
    datasets = [
        xr.open_dataset(p).sortby("time") for p in to_paths(
            cams_data=data,
            extract_dir=extract_dir,
        )
    ]
    logger.debug("Opened %d datasets.", len(datasets))

    level_dataset, surface_dataset = identify(datasets)

    if level_dataset is None:  # pragma: no cover
        raise ValueError("Could not find a multi-level dataset.") 

    # Select in time and space
    selected = select(level_dataset, time, longitude.m, latitude.m)

    pressure_data = "surface_pressure" if pressure_data is None else pressure_data

    # Read surface pressure if available
    if surface_dataset is not None:
        surface_selected = select(surface_dataset, time, longitude.m, latitude.m)
        if "sp" in surface_selected:
            surface_pressure = to_quantity(surface_selected["sp"])
        else:
            if pressure_data == "surface_pressure":  # pragma: no cover
                raise ValueError(
                    "Could not found a 'sp' surface pressure data variable "
                    "in the surface dataset."
                    "This is required when the option 'pressure_data' is set "
                    "to 'surface_pressure'."
                )
            surface_pressure = None  # pragma: no cover
    else:
        if pressure_data == "surface_pressure":  # pragma: no cover
            raise ValueError(
                "The CAMS surface dataset could not be found. "
                "As a result, the surface pressure cannot be fetched."
                "This is required when the option 'pressure_data' is set to "
                "'surface_pressure'."
            )
        else:
            surface_pressure = None  # pragma: no cover

    if surface_pressure is not None:  # pragma: no cover
        logger.info("Surface pressure: %s", f"{surface_pressure:~P}")

    # Translate model levels into altitude values (and add pressure data)
    altitude_dataset = model_level_to_altitude(
        selected,
        pressure_data=pressure_data,
        surface_pressure=surface_pressure,
    )

    # Create a data structure storing mole fractions
    data = mole_fractions(altitude_dataset)

    # Drop extra molecules
    if molecules:
        data = data.drop_vars(
            [
                xm for xm in data
                if xm.startswith("x_") and xm not in [
                    f"x_{m}" for m in molecules
                ]
            ]
        )

    # compute missing molecules
    if molecules:
        missing_molecules = [m for m in molecules if f"x_{m}" not in data]
        logger.debug(
            "The following requested molecules are not in the CAMS data: %s",
            ", ".join(missing_molecules),
        )

        if missing_molecules and not missing_molecules_from:
            raise ValueError(
                "Missing molecules were requested but no reference dataset "
                "was provided."
            )
    
    # add missing molecules
    if missing_molecules_from is not None:
        _data = missing_molecules_from.drop_vars([
            v for v in missing_molecules_from.data_vars
            if not v.startswith("x_")
        ])

        _all_molecules = [x[2:] for x in _data.data_vars]
        _drop_molecules = [
            m for m in _all_molecules
            if m not in missing_molecules
        ]
        _missing_data = _data.drop_vars([
            f"x_{m}" for m in _drop_molecules
        ])
    
        logger.debug("data z units: %s", data.z.units)
        # missing molecule data must be on the same altitude grid
        _missing_data = _missing_data.interp(
            z=data.z.values,
        )

        # missing molecule data can be added
        data = data.assign(
            **{
                f"x_{m}": _missing_data[f"x_{m}"]
                for m in missing_molecules
            }
        )

    # add pressure and temperature data
    data = data.assign(
        {
            "p": (
                    "z",
                    altitude_dataset["p"].values,
                    {"units": altitude_dataset["p"].units},
                ),
            "t": (
                    "z",
                    altitude_dataset["t"].values,
                    {"units": altitude_dataset["t"].units},
                ),
        }
    )


    # Dataset attributes
    INSTITUTION = "European Centre for Medium-Range Weather Forecasts (ECMWF)"
    SOURCE = (
        "4DVar data assimilation in CY42R1 of ECMWF’s Integrated Forecast "
        "System (IFS)"
    )

    utcnow = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    # This comment follows the Copernicus Products Licence Agreement requirements:
    # https://cds.climate.copernicus.eu/api/v2/terms/static/licence-to-use-copernicus-products.pdf
    COMMENT = (
        "Downloaded from the Copernicus Atmosphere Monitoring Service (CAMS) "
        "Atmosphere Data Store (ADS) (<URL to dataset overview page>)"
        "Contains modified Copernicus Atmosphere Monitoring Service information "
        "2023. Neither the European Commission nor ECMWF is responsible for any "
        "use that may be made of the Copernicus information or data it contains."
    )

    # Citing
    # https://confluence.ecmwf.int/display/CKB/CAMS%3A+Reanalysis+data+documentation#CAMS:Reanalysisdatadocumentation-HowtocitetheCAMSGlobalReanalysis

    # Overview pages URLs
    URL = {
        "EAC4": "https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-reanalysis-eac4?tab=overview",
        "EGG4": "https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-ghg-reanalysis-egg4?tab=overview",
    }
    acknowledgment = (
        f"Downloaded from the Copernicus Atmosphere Monitoring Service (CAMS) "
        f"Atmosphere Data Store (ADS) ({URL[identifier]})"
    )

    # Published / web-based references
    REFERENCE = {
        "EAC4": "https://doi.org/10.5194/acp-19-3515-2019",
        "EGG4": "https://confluence.ecmwf.int/display/CKB/CAMS%3A+Reanalysis+data+documentation"
    }

    URL_DATE = {
        "EAC4": "2023-06-16",
        "EGG4": "2023-06-16",
    }

    ds = schema.convert(
        data_vars={
            "p": to_quantity(data.p),
            "t": to_quantity(data.t),
            **{
                xm: to_quantity(data[xm])
                for xm in data if xm.startswith("x_")
            },
        },
        coords={
            "z": to_quantity(data.z),
        },
        attrs={
            "title": "CAMS global reanalysis (EAC4) atmospheric profile",
            "institution": INSTITUTION,
            "source": SOURCE,
            "history": f"{utcnow} - CAMS data converted to Joseki format",
            "references": REFERENCE[identifier],
            "comment": COMMENT,
            "acknowledgment": acknowledgment,
            "url": URL[identifier],
            "urldate": URL_DATE[identifier],
            "latitude": f"{latitude:~}",
            "longitude": f"{longitude:~}",
            "Conventions": "CF-1.10",
        }
    )

    if extrapolate:
        #z = to_quantity(ds.z)
        extrapolate_up = extrapolate.get("up", None)
        extrapolate_down = extrapolate.get("down", None)

        if extrapolate_up is None and extrapolate_down is None:
            raise ValueError("Either 'up' or 'down' must be specified.")

        if extrapolate_up:
            z_up = extrapolate_up.get("z", None)
            method_up = extrapolate_up.get("method", {"default": "nearest"})
            ds = _extrapolate(
                ds=ds,
                direction="up",
                z_extra=z_up,
                method=method_up,
            )
        if extrapolate_down:
            z_down = extrapolate_down.get("z", None)
            method_down = extrapolate_down.get("method", {"default": "linear"})
            ds = _extrapolate(
                ds=ds,
                direction="down",
                z_extra=z_down,
                method=method_down,
            )
    else:
        ds = ds

    if regularize:
        z = to_quantity(ds.z)
        default_num = int((z.max() - z.min()) // np.diff(z).min())
        if isinstance(regularize, bool):
            regularize = {}
        ds = _regularize(
            ds=ds,
            method=regularize.get("method", DEFAULT_METHOD),
            conserve_column=regularize.get("conserve_column", False),
            options=regularize.get('options', {"num": default_num}),
        )
    else:
        ds = ds
    
    return ds


# TODO: add support for .tar.gz archives
def from_archive(path: Path, extract_dir : Path | None = None) -> Path:
    """Extract archive file and return directory with extracted files.

    Args:
        path: Path to the archive file.
        extract_dir: Directory where to place the extracted files. If unset,
            a temporary directory is created.
    Returns:
        Directory with extracted files.
    """
    
    if extract_dir is None:
        tmpdir = tempfile.mkdtemp()
        extract_dir = Path(tmpdir)

    logger.info("Extracting archive to %s", extract_dir.absolute())
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        extracted_files = [_ for _ in extract_dir.glob("*.nc")]

    logger.debug("Completed extraction.")
    for file in extracted_files:
        filesize = os.path.getsize(file) * ureg.byte
        filesize_repr = f"{filesize.to('gigabyte'):.3f~}"
        logger.debug("File: %s. Size: %s", file, filesize_repr)

    return extract_dir


def to_paths(
    cams_data: PathLike | list[PathLike],
    extract_dir : Path | None = None,
) -> list[Path]:
    """
    Convert input to paths to CAMS dataset(s).

    Args:
        cams_data: path(s) to NetCDF file(s) (.nc), path to directory with NetCDF 
            files or path to archive file (.zip).
        extract_dir: Directory where to place the extracted files. If unset,
            a temporary directory is created.
    
    Returns:
        List of paths.
    
    Notes:
        `path` could be the path to the CAMS archive file (.zip), in which 
        case the archive file is extracted in a temporary folder and the 
        ectracted files loaded into datasets.
        `path` could also be the path to the directory with the extracted 
        files (.nc).
        Finally, `path` could be the path to an individual NetCDF file.
    """
    _dir = None

    # Single path
    if isinstance(cams_data, (str, Path)):
        cams_data = Path(cams_data)
        if not cams_data.exists():
            raise FileNotFoundError(
                f"File or directory not found: {cams_data.absolute()}"
            )

        # File
        if cams_data.is_file():

            # Archive file
            if cams_data.name.endswith(".zip"):
                _dir = from_archive(path=cams_data, extract_dir=extract_dir)
                filepaths = [_ for _ in _dir.glob("*.nc")]

            # NetCDF file
            elif cams_data.name.endswith(".nc"):
                filepaths = [cams_data]
            
            else:  # pragma: no cover
                raise NotImplementedError(
                    f"Expected a path name ending with '.zip' or with '.nc' "
                    f"(got {cams_data})."
                )
        
        # Directory
        else:
            filepaths = [_ for _ in cams_data.glob("*.nc")]

    # List of paths
    elif isinstance(cams_data, list):
        filepaths = [Path(x) for x  in cams_data]
    
    else:
        raise NotImplementedError(
            f"Expected type for 'path' to be either a Path or a list of Path "
            F"(got {type(cams_data)})."
        )
    
    logger.info("filepaths=%s", [x.absolute() for x in filepaths])

    return filepaths 


def identify(datasets: list) -> tuple:
    """Identify the level and surface datasets from a list of datasets.

    Args:
        datasets: List of datasets (1 or 2).
    
    Returns:
        Tuple of level and surface datasets.
    """
    try:
        assert len(datasets) in [1, 2]
    except AssertionError as e:  # pragma: no cover
        msg = f"Expected 1 or 2 datasets, got {len(datasets)}"
        logger.critical(msg)
        raise ValueError(msg) from e

    # look for the model level dataset ('level' coordinate)
    level_dataset = None
    surface_dataset = None
    for dataset in datasets:
        if "level" in dataset.coords:
            level_dataset = dataset
        else:
            surface_dataset = dataset
    
    return level_dataset, surface_dataset


def select(
    ds: xr.Dataset,
    datetime: str | datetime.datetime | np.datetime64,
    lon: float,
    lat: float,
):
    """Select a CAMS dataset at specific datetime, longitude and latitude.
    
    Args:
        ds: CAMS Dataset.
        datetime: Datetime.
        lon: Longitude [degrees].
        lat: Latitude [degrees].

    Notes:
        The dataset is selected using the nearest method.
    """
    _ds = ds.sel(time=datetime, method="nearest", drop=True)
    _ds = _ds.sel(latitude=lat, longitude=lon, method="nearest", drop=True)
    return _ds


def getpath(filename: str) -> Path:
    """
    Get path for data file.

    Args:
        filename: File name.

    Returns:
        Path to data file.
    """
    return importlib_resources.files("joseki.data.ecmwf").joinpath(filename)


def rescale_pressure_profile(
    ds: xr.Dataset,
    surface_pressure: pint.Quantity
) -> xr.Dataset:
    """Rescale pressure profile with surface pressure.
    
    Args:
        ds: Dataset with pressure profile.
        surface_pressure: Surface pressure.
    
    Returns:
        Dataset with rescaled pressure profile.

    Notes:
        The pressure profile is multiplied by a scaling factor such that
        the surface pressure matches the provided surface pressure.
    """
    logger.debug("Rescaling pressure data with surface pressure")
    ds_surface_pressure = to_quantity(ds.p.sel(z=0, method="nearest"))
    logger.debug("Surface pressure: %s", ds_surface_pressure)
    scaling_factor = (
        surface_pressure / ds_surface_pressure
    ).m_as("dimensionless")
    logger.debug("Scaling factor: %s", scaling_factor)
    with xr.set_options(keep_attrs=True):
        ds["p"] = ds["p"] * scaling_factor
    return ds


# TODO: the model level to altitude conversion is approximated
def model_level_to_altitude(
    ds: xr.Dataset,
    pressure_data: str = "model_level_60",
    surface_pressure: pint.Quantity | None = None,
) -> xr.Dataset:
    """
    Convert model level data to altitude data and add pressure data.

    Args:
        ds: Dataset with model level data.
        pressure_data: indicates how to compute the pressure data. Either
            'model_level_60' or 'surface_pressure'. If 'model_level_60',
            the pressure data is computed from the L60 model level table.
            If 'surface_pressure', the pressure data is computed by rescaling
            the L60 model level table with the surface pressure from the CAMS
            surface dataset.
        surface_pressure: Surface pressure from the CAMS surface dataset.
            Serves to compare with L60 model level pressure data and report
            on discrepancies (this discrepancies become large over 
            high-altitude regions). If None, these discrepancies are not
            reported.
    
    Returns:
        Dataset tabulated against altitude and with pressure data.

    Notes:
        The relationship between model level and (geometric) altitude is 
        documented on the page 
        [L60 model level definitions](https://confluence.ecmwf.int/display/UDOC/L60+model+level+definitions).
        A table can be downloaded which maps the model level and (geometric) 
        altitude values. 
        This table is read it into a pandas data frame.
        From the dataframe, we create a xarray data array that tabulates the 
        model level against geometric altitude.
        We use the DataArray object to interpolate our model level datasets.
        In the process, the pressure data corresponding to the model level is 
        added.
        If pressure_data is set to 'surface_pressure', we rescale the pressure
        data with the surface pressure from the CAMS surface dataset.
        Last, we sort the data by increasing altitude value.
        This transformation is not accurate.
    """
    l60_path = getpath(filename="model_levels_60.csv")
    df = pd.read_csv(l60_path)
    level = xr.DataArray(
        df["n"].values[1:],
        dims=["z"],
        coords={
            "z": (
                "z",
                np.array(df["Geometric Altitude [m]"].values[1:], dtype=float),
                {"units": "m"},
            )
        },
    )

    # first, drop any variable called 'z' as that 
    ds = ds.drop_vars("z") if "z" in ds else ds

    interpolated = ds.interp(level=level).drop_vars("level")
    ds = interpolated.assign(
        {
            "p": (
                "z",
                np.array(df["pf [hPa]"].values[1:], dtype=float),
                {"units": "hPa"},
            ),
        }
    ).sortby("z")

    # Ensure altitude are in kilometer
    z = to_quantity(ds.z)
    ds = ds.assign({
        "z": ("z", z.m_as("km"), {"units": "km", "long_name": "altitude"})
    })

    if pressure_data == "surface_pressure":  # pragma: no cover
        rescale_pressure_profile(ds, surface_pressure)

    # Report on surface pressure discrepancy
    if surface_pressure is not None:  # pragma: no cover
        ds_surface_pressure = to_quantity(ds.p.sel(z=0, method="nearest"))
        rel_diff = (ds_surface_pressure - surface_pressure) / surface_pressure
        logger.info(
            "Dataset lower level pressure, %s",
            f"{ds_surface_pressure:~P}",
        )
        logger.info(
            "Surface pressure from CAMS surface dataset, %s",
            f"{surface_pressure:~P}",
        )
        logger.info(
            "Surface pressure discrepancy: %s",
            f"{rel_diff.m_as('1'):.1%}",
        )

    return ds


def mole_fractions(ds: xr.Dataset) -> xr.DataArray:
    """Get the mole fractions data from a dataset.

    Args:
        ds: Input dataset.

    Returns:
        Mole fractions dataset.
    
    Notes:
        Assumes that the input dataset tabulates the specific ratios as a
        function of altitude (coordinate 'z').
    """
    logger.debug("Extracting mole fraction from dataset")

    # List molecules in dataset
    molecules_cams = [m for m in ds.data_vars if m in MOLECULE]
    molecules_joseki = [MOLECULE[m] for m in molecules_cams]

    # Mass mixing ratio as a function of molecule and altitude
    y = xr.DataArray(
        data=np.atleast_2d(
            np.stack(
                [
                    ds[x].values
                    for x in molecules_cams
                ]
            )
        ),
        coords={
            "m": ("m", molecules_joseki),
            "z": ds["z"],
        }
    )

    # Convert mass mixing ratio to mole mixing ratio
    x = mass_fraction_to_mole_fraction3(y=y)

    # Re-organise the `xarray.DataArray` into a `xarray.Dataset` with one 
    # data variable per molecule mole fraction
    return to_m_suffixed_data(x)


def get_molecule_amounts(
    data: PathLike | list[PathLike],
    time: str | datetime.datetime | np.datetime64,
    lon: float | pint.Quantity,
    lat: float | pint.Quantity,
    molecules: list[str] | None = None,
    extract_dir : Path | None = None
) -> dict:
    """Get molecule amount from CAMS data.

    Args:
        data: Path to CAMS data or list of paths to CAMS data.
        time: Time.
        lon: Longitude [degrees].
        lat: Latitude [degrees].
        molecules: List of molecules to extract. If None, all molecules are
            extracted.
        extract_dir: Directory where to extract the data. If None, the data
            is extracted in a temporary directory.
    
    Raises:
        ValueError: If the molecule is not available in the dataset.
    
    Returns:
        Mapping of molecule and amount.

    Notes:
        The mapping is suitable for use with `joseki.accessor.rescale_to`.
    """
    longitude = to_quantity(lon, units="degree")
    latitude = to_quantity(lat, units="degree")

    # Open datasets (we sort by time because CAMS data is not always sorted by 
    # time and this is required to select at a timestamp)
    datasets = [
        xr.open_dataset(p).sortby("time") for p in to_paths(
            cams_data=data,
            extract_dir=extract_dir,
        )
    ]
    logger.debug("Opened %d datasets.", len(datasets))

    _, surface_dataset = identify(datasets)

    # Select in time and space
    selected = select(surface_dataset, time, longitude.m, latitude.m)

    amount = {}
    for dv in selected.data_vars:
        try:
            m = MOLECULE_TOTALS[dv]
        except KeyError:  # pragma: no cover
            pass
        else:
            amount[m] = to_quantity(selected[dv])
    
    # check that all molecules are present
    if molecules is not None:
        for m in molecules:
            if m not in amount:
                raise ValueError(f"Molecule {m} not found in dataset.")
    
    # drop all molecules that are not requested
    if molecules is not None:
        amount = {m: amount[m] for m in molecules}
    
    return amount
