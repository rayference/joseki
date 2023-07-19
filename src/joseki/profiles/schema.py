"""Dataset schema for atmosphere thermophysical profiles.

The dataset schema defines the variables, coordinates and attributes that are
expected in a dataset representing an atmosphere thermophysical profile.
"""
from __future__ import annotations

import logging
import typing as t

from attrs import define
import numpy as np
import xarray as xr
import pint
from functools import singledispatch

from ..__version__ import __version__
from ..units import ureg, to_quantity
from .util import utcnow, number_density

logger = logging.getLogger(__name__)

REQUIRED_DIMS = {"time", "latitude", "longitude", "z"}
# no other dimension is allowed

REQUIRED_ATTRS = {
    "Conventions",
    "title",
    "institution",
    "source",
    "history",
    "references",
}
# additional attributes are allowed

REQUIRED_COORDS = {"time", "latitude", "longitude", "z"}
# no other coordinate is allowed

REQUIRED_DATA_VARS = {"p", "t", "n"}
# at least one mole fraction data variable (starting with 'x_') is required
# additional data variable are allowed

ATTRIBUTES = {
    "z": {
        "standard_name": "altitude",
        "long_name": "altitude",
    },
    "time": {
        "standard_name": "time",
        "long_name": "time",
    },
    "longitude": {
        "standard_name": "longitude",
        "long_name": "longitude",
    },
    "latitude": {
        "standard_name": "latitude",
        "long_name": "latitude",
    },
    "p": {
        "standard_name": "air_pressure",
        "long_name": "air pressure",
    },
    "t": {
        "standard_name": "air_temperature",
        "long_name": "air temperature",
    },
    "n": {
        "standard_name": "air_number_density",
        "long_name": "air number density",
    },
    "x_M": {
        "standard_name": "M_mole_fraction",
        "long_name": "M mole fraction",
    }
}

DIMENSIONALITY = {
    "z": "[length]",
    "time": "[time]",
    "longitude": "[angle]",
    "latitude": "[angle]",
    "p": "[mass] [length]^-1 [time]^-2",
    "t": "[temperature]",
    "n": "[length]^-3",
    "x_M": "dimensionless",  # Warning, discriminate between mole/mole 
    # (mole fraction) and kg/kg (mass fraction)
}

UNITS = {
    # time has not units because they are timestamps
    "latitude": "deg",
    "longitude": "deg",
    "z": "km",
    "p": "Pa",
    "t": "K",
    "n": "m^-3",
    "x_M": "dimensionless",
}

DATA_TYPE = {}  # TODO: fill this dict


def history() -> str:
    return f"{utcnow()} dataset formatting by joseki version {__version__}."

def default_attrs() -> dict:
    history = f"{utcnow()} - dataset creation by joseki version {__version__}."
    return {
        "Conventions": "CF-1.10",
        "title": "Unknown",
        "institution": "Unknown",
        "source": "Unknown",
        "history": history,
        "references": "Unknown",
    }

def mole_fraction_sum(ds: xr.Dataset) -> pint.Quantity:
    """Compute the sum of mole fractions.

    Args:
        ds: Dataset.

    Returns:
        The sum of mole fractions.
    """
    return (
        sum([ds[c] for c in ds.data_vars if c.startswith("x_")]).values
        * ureg.dimensionless
    )

@define(frozen=True)
class Schema:
    """Dataset schema for atmosphere thermophysical profiles."""

    def convert(self, data: t.Any) -> xr.Dataset:
        return convert(data)

    def validate(
        self,
        ds: xr.Dataset,
        check_x_sum: bool = False,
        ret_true_if_valid: bool = False,
    ) -> None | bool:
        return validate_dataset(
            ds,
            check_x_sum=check_x_sum,
            ret_true_if_valid=ret_true_if_valid,
        )
    

@singledispatch
def convert(data: t.Any) -> xr.Dataset:
    raise NotImplementedError

@convert.register(dict)
def _(data: dict) -> xr.Dataset:
    return convert_dict(data)

@convert.register(xr.Dataset)
def _(data: xr.Dataset) -> xr.Dataset:
    return convert_dataset(data)


def convert_dict(data: dict) -> xr.Dataset:
    """Convert dictionary to schema-compliant dataset.
    
    Args:
        data: Mapping of variable names and to quantities and dataset 
            attributes to their values.
    
    Returns:
        Schema-compliant dataset.
    """
    dims = list(REQUIRED_DIMS)
    shape = tuple([len(data[dim]) for dim in dims])
    
    # Coordinates
    coords = {}
    for coord in REQUIRED_COORDS:
        if coord != "time":
            attrs = ATTRIBUTES[coord]
            attrs.update({"units": f"{data[coord].units}"})
            coords[coord] = (coord, data[coord].m_as(UNITS[coord]), attrs)
        else:
            coords[coord] = (coord, data[coord], ATTRIBUTES[coord])
    
    # Data variables
    data_vars = {}
    for data_var in REQUIRED_DATA_VARS:
        attrs = ATTRIBUTES[data_var]
        attrs.update({"units": f"{data[data_var].units}"})
        data_vars[data_var] = (
            dims,
            data[data_var].reshape(shape).m_as(UNITS[data_var]),
            attrs,
        )
    
    for key in data:
        if key.startswith("x_"):
            molecule_formula = key[2:]
            attrs = ATTRIBUTES["x_M"]
            standard_name, long_name = attrs["long_name"], attrs["standard_name"]
            long_name = long_name.replace("M", molecule_formula)
            standard_name = standard_name.replace("M", molecule_formula)
            units = data[key].units
            data_vars[key] = (
                dims,
                data[key].reshape(shape).m_as(UNITS["x_M"]),
                {
                    "standard_name": standard_name,
                    "long_name": long_name,
                    "units": f"{units:~}",
                },
            )

    # Attributes
    attrs_keys = []
    for key in list(data.keys()):
        if key not in coords and key not in data_vars:
            attrs_keys.append(key)
    attrs = default_attrs()
    attrs.update({key: data[key] for key in attrs_keys})

    
    return xr.Dataset(
        data_vars=data_vars,
        coords=coords,
        attrs=attrs,
    )
    

def convert_dataset(ds: xr.Dataset) -> xr.Dataset:
    """
    Convert a dataset to a schema-compliant dataset.

    Args:
        ds: Dataset to convert.
    
    Returns:
        Dataset with schema-compliant data variables, coordinates, and
        attributes.
    
    Raises:
        ValueError: If the dataset cannot be converted.
    
    Notes:
        The input dataset is assumed to included all required dimensions, 
        coordinates, and data variables (except 'n').
        Missing variables' attribute will be added if missing.
        Missing dataset' attributes will be added and their values set to 
        'Unknown'.
    """
    # 1. add 'n' if missing
    if "n" not in ds.data_vars:
        n = number_density(
            p=to_quantity(ds.p),
            t=to_quantity(ds.t),
        )
        ds["n"] = (ds.p.dims, n, {"units": n.units})

    # 2. update variables' attributes
    for var in ATTRIBUTES:
        ds.data_vars[var].attrs.update(ATTRIBUTES[var])

    # 3. update dataset attributes
    attrs = default_attrs()
    ds_attrs = ds.attrs
    attrs.update(ds_attrs)  # override 'attrs' with 'ds_attrs'
    ds.attrs = attrs

    return ds
    

def validate_dataset(
    ds: xr.Dataset,
    check_x_sum: bool = False,
    ret_true_if_valid: bool = False,
) -> None | bool:
    """
    Check that dataset is compliant with schema.

    Args:
        ds: Dataset to validate.
        check_x_sum: if True, check that mole fraction sums
            are never larger than one.
        ret_true_if_valid: make this method return True if the dataset is
            valid.

    Returns:
        None or bool: If `ret_true_if_valid` is True, returns True if the 
            dataset is valid, otherwise returns None.            

    Raises:
        ValueError: If the dataset does not match the schema.

    Notes:
        Add variable attributes ('standard_name' and 'long_name') if missing.
    """
    # TODO: lazy mode: accumulate errors and raise once (if need be)
    logger.debug("Validating dataset")

    # Dimensions
    logger.debug("checking that dataset dims enclose required dims")
    if not REQUIRED_DIMS == set(ds.dims):
        raise ValueError(  # pragma: no cover
            f"missing dimension(s): {REQUIRED_DIMS - set(ds.dims)}"
        )

    # Coordinates
    logger.debug("checking that all required coordinates are present")
    if not REQUIRED_COORDS == set(ds.coords):
        raise ValueError(  # pragma: no cover
            f"missing coordinate(s): {REQUIRED_COORDS - set(ds.coords)}"
        )
    
    # Dimensionalities
    logger.debug("checking that dimensionalities are correct")
    for coord in REQUIRED_COORDS:
        pass
    for data_var in REQUIRED_DATA_VARS:
        pass
    
    # Data variables
    logger.debug("checking that all required data variables are present")
    if not REQUIRED_DATA_VARS.issubset(set(ds.data_vars)):
        raise ValueError(  # pragma: no cover
            f"missing data variable(s): {REQUIRED_DATA_VARS - set(ds.data_vars)}"
        )
    
    if not any([name.startswith("x_") for name in ds.data_vars]):
        raise ValueError(
            "missing mole fraction data variable (starting with 'x_')"
        )

    # Dataset attributes
    logger.debug("checking that all attributes are present")
    if not REQUIRED_ATTRS.issubset(set(ds.attrs)):
        raise ValueError(  # pragma: no cover
            f"missing attribute(s): {REQUIRED_ATTRS - set(ds.attrs)}"
        )

    # Mole fraction sum
    if check_x_sum:
        logger.debug(
            "Checking that the mole fraction sum is never larger than one"
        )
        mfs = mole_fraction_sum(ds)
        if np.any(mfs.m > 1):
            raise ValueError(  # pragma: no cover
                "Mole fraction sum is not always less or equal to one."
            )
        # TODO: indicate where (longitude, latitude, time, z) the sum is larger 
        # than one

    logger.info("Dataset is valid")

    if ret_true_if_valid:  # pragma: no cover
        return True


schema = Schema()
