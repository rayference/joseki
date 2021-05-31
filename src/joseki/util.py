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
