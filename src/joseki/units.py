"""Units module."""
import pint
import xarray as xr

ureg = pint.UnitRegistry()

# define ppmv unit
ureg.define("ppmv = 1e-6 * m^3 / m^3")

# define dobson unit
ureg.define("dobson_unit = 2.687e20 * meter^-2 = du = dobson = dobson_units")


def to_quantity(da: xr.DataArray) -> pint.Quantity:  # type: ignore [type-arg]
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
