"""Units module."""
from __future__ import annotations

from functools import singledispatch
import logging

import pint
import numpy as np
import xarray as xr
from numpy.typing import ArrayLike

logger = logging.getLogger(__name__)

ureg = pint.get_application_registry()

definitions = [
    # (mole) fraction
    "@alias ppm = parts_per_million = ppmv",
    "parts_per_billion = 1e-9 = ppb = ppbv",
    "parts_per_trillion = 1e-12 = ppt = pptv",

    # column number density
    "dobson_unit = 2.687e20 * meter^-2 = du = dobson_units",
]

for definition in definitions:
    try:
        ureg.define(definition)
    except pint.RedefinitionError:  # pragma: no cover
        logger.warning("unit definition '%s' already exists", definition)


@singledispatch
def to_quantity(
    value: pint.Quantity | dict | int | float | list | np.ndarray | xr.DataArray,
    units: None | str = None,
) -> pint.Quantity:
    """Convert to a `pint.Quantity`.

    Args:
        value: Value which will be converted. If value is an `ArrayLike`, it is
            assumed to be dimensionless (unless `units` is set).
            If a `xarray.DataArray` is passed and 
            `units_error` is `True`, it is assumed to have a `units` key in
            its `attrs` field; otherwise, it is assumed to be dimensionless.
        units: Units to assign. If `None`, the units are inferred from the
            `value` argument.

    Returns:
        The corresponding quantity.
    
    Notes:
        This function can also be used on DataArray and Dataset coordinate 
        variables.
    """
    raise NotImplementedError

@to_quantity.register(pint.Quantity)
def d(
    value, 
    units: None | str = None,
) -> pint.Quantity:
    return value.to(units) if units else value

@to_quantity.register(dict)
def d(
    value,
    units: None | str = None,
) -> pint.Quantity:
    return ureg.Quantity(**value).to(units) if units else ureg.Quantity(**value)

@to_quantity.register(int)
def d(
    value,
    units: None | str = None,
) -> pint.Quantity:
    return to_quantity_array_like(value, units)

@to_quantity.register(float)
def d(
    value,
    units: None | str = None,
) -> pint.Quantity:
    return to_quantity_array_like(value, units)

@to_quantity.register(list)
def d(
    value,
    units: None | str = None,
) -> pint.Quantity:
    return to_quantity_array_like(np.array(value), units)

@to_quantity.register(np.ndarray)
def d(
    value,
    units: None | str = None,
) -> pint.Quantity:
    return to_quantity_array_like(value, units)

@to_quantity.register(xr.DataArray)
def d(
    value: xr.DataArray,
    units: None | str = None,
) -> pint.Quantity:
    try:
        da_units = value.attrs["units"]
    except KeyError as e:
        if units is None:
            raise ValueError(
                "this DataArray has no 'units' metadata field"
            ) from e
        else:
            return value.values * ureg(units)
    else:
        q = value.values * ureg(da_units)
        if units is not None:
            return q.to(units)
        else:
            return q
    

def to_quantity_array_like(
    value: ArrayLike,
    units: None | str = None,
) -> pint.Quantity:
    try:
        magnitude = np.array(value)
    except ValueError as e:  # pragma: no cover
        raise TypeError(
            f"Could not convert this type ({type(value)}) to a numpy array"
        ) from e
    else:
        if units is not None:
            return magnitude * ureg(units)
        else:
            return magnitude * ureg.dimensionless
