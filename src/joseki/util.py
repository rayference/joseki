"""Utility module."""
import datetime
from typing import Any
from typing import Dict
from typing import Hashable
from typing import Optional
from typing import Union

import numpy as np
import pint
import xarray as xr

from .units import ureg


@ureg.wraps(
    ret=None,
    args=(
        "Pa",
        "K",
        "m^-3",
        "",
        "km",
        "",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ),
    strict=False,
)
def make_data_set(
    p: Union[pint.Quantity, np.ndarray],  # type: ignore[type-arg]
    t: Union[pint.Quantity, np.ndarray],  # type: ignore[type-arg]
    n: Union[pint.Quantity, np.ndarray],  # type: ignore[type-arg]
    x: Union[pint.Quantity, np.ndarray],  # type: ignore[type-arg]
    z: Union[pint.Quantity, np.ndarray],  # type: ignore[type-arg]
    molecules: Union[pint.Quantity, np.ndarray],  # type: ignore[type-arg]
    convention: str = "CF-1.8",
    title: str = "unknown",
    history: Optional[str] = None,
    func_name: str = "unknown",
    operation: str = "unknown",
    source: str = "unknown",
    references: str = "unknown",
    url: Optional[str] = None,
    url_date: Optional[str] = None,
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

    x: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Volume mixing ratios [/].

    z: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Altitude [km].

    molecules: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Molecules [/].

    convention: str
        Metadata convention.

    title: str
        A succinct description of what is in the dataset.

    history: str, optional
        Provides an audit trail for modifications to the original data.

    func_name: str
        Name of the calling function.

    operation: str
        Name of the operation performed on the data set.

    source: str
        The method of production of the original data.

    references: str
        Published or web-based references that describe the data or methods
        used to produce it.

    url: str, optional
        Data URL.

    url_date: str, optional
        Date and time of last access to URL.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    if history is None:
        history = f"{datetime.datetime.utcnow()}" f"- {operation} - {func_name}\n"
    else:
        history += f"{datetime.datetime.utcnow()} " f"- {operation} - {func_name}\n"
    attrs: Dict[Hashable, Any] = dict(
        convention=convention,
        title=title,
        history=history,
        source=source,
        references=references,
    )
    if url is not None:
        attrs.update(dict(url=url))
    if url_date is not None:
        attrs.update(dict(url_date=url_date))

    return xr.Dataset(
        data_vars=dict(
            p=(
                "z",
                p,
                dict(
                    standard_name="air_pressure",
                    long_name="air pressure",
                    units="Pa",
                ),
            ),
            t=(
                "z",
                t,
                dict(
                    standard_name="air_temperature",
                    long_name="air temperature",
                    units="K",
                ),
            ),
            n=(
                "z",
                n,
                dict(
                    standard_name="air_number_density",
                    long_name="air number density",
                    units="m^-3",
                ),
            ),
            x=(
                ("molecules", "z"),
                x,
                dict(
                    standard_name="volume_mixing_ratio",
                    long_name="volume mixing ratio",
                    units="",
                ),
            ),
        ),
        coords=dict(
            z=(
                "z",
                z,
                dict(
                    standard_name="altitude",
                    long_name="altitude",
                    units="km",
                ),
            ),
            molecules=(
                "molecules",
                molecules,
                dict(
                    standard_name="molecules",
                    long_name="molecules",
                    units="",
                ),
            ),
        ),
        attrs=attrs,
    )


def to_quantity(da: xr.DataArray) -> pint.Quantity:
    """Convert a :class:`~xarray.DataArray` to a :class:`~pint.Quantity`.

    The array's ``attrs`` metadata mapping must contain a ``units`` field.

    .. note:: This function can also be used on coordinate variables.

    Parameters
    ----------
    da: :class:`~xarray.DataArray`
        :class:`~xarray.DataArray` instance which will be converted.

    Returns
    -------
    :class:`~pint.Quantity`:
        The corresponding :class:`~pint.Quantity`.

    Raises
    ------
    ValueError:
        If the :class:`~xarray.DataArray`'s ``attrs`` does not contain a ``units`` key.
    """
    try:
        units = da.attrs["units"]
    except KeyError as e:
        raise ValueError("this DataArray has no 'units' metadata field") from e
    else:
        return ureg.Quantity(da.values, units)


CFC_FORMULAE = {
    "CCl3F": ("Freon-11", "F11", "R-11", "CFC-11"),
    "CCl2F2": ("Freon-12", "F12", "R-12", "CFC-12"),
    "CClF3": ("Freon-13", "F13", "R-13", "CFC-13"),
    "CF4": ("Freon-14", "F14", "CFC-14"),
    "CHClF2": ("Freon-22", "F22", "HCFC-22"),
    "CHCl2F": ("Freon-21", "F21", "HCFC-21"),
    "C2Cl3F3": ("Freon-113", "F113", "CFC-113"),
    "C2Cl2F4": ("Freon-114", "F114", "CFC-114"),
}


def to_chemical_formula(name: str) -> str:
    """Convert to chemical formula.

    If molecule name is unknown, returns name unchanged.

    Parameters
    ----------
    name: str
        Molecule name.

    Returns
    -------
    str:
        Molecule formula.
    """
    try:
        return translate_cfc(name)
    except ValueError:
        return name


def translate_cfc(name: str) -> str:
    """Convert chlorofulorocarbon name to corresponding chemical formula.

    Parameters
    ----------
    name: str
        Chlorofulorocarbon name.

    Returns
    -------
    str:
        Chlorofulorocarbon chemical formula.

    Raises
    ------
    ValueError:
        If the name does not match a known chlorofulorocarbon.
    """
    for formula, names in CFC_FORMULAE.items():
        if name in names:
            return formula
    raise ValueError("Unknown chlorofulorocarbon {name}")
