"""Utility module."""
import pint
import xarray as xr

from joseki import ureg


def add_comment(ds: xr.Dataset, comment: str) -> None:
    """Add a comment to a :class:`~xarray.Dataset`'s ``attrs``.

    If a comment already exists, the new comment is appended to the previous
    comments.

    Parameters
    ----------
    ds: :class:`xarray.Dataset`
        Data set.

    comment: str
        Comment to add.
    """
    try:
        previous_comment = ds.attrs["comment"]
        ds.attrs.update(dict(comment=f"{previous_comment}\n{comment}"))
    except KeyError:
        ds.attrs.update(dict(comment=comment))


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
    "CF4": ("Freon-14", "F4", "CFC-14"),
    "CHClF2": ("Freon-22", "F22", "HCFC-22"),
    "CHCl2F": ("Freon-21", "F21", "HCFC-21"),
    "C2Cl3F3": ("Freon-113", "F113", "CFC-113"),
    "C2Cl2F4": ("Freon-114", "F114", "CFC-114"),
}


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
        If the chlorofulorocarbon is unknown.
    """
    for formula, names in CFC_FORMULAE.items():
        if name in names:
            return formula
    raise ValueError(f"Unknown name {name}")
