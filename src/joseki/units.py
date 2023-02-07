"""Units module."""
import pint
import xarray as xr

ureg = pint.UnitRegistry()

# define ppm unit
ureg.define("parts_per_million = 1e-6 = ppm = ppmv")

# define dobson unit
ureg.define("dobson_unit = 2.687e20 * meter^-2 = du = dobson = dobson_units")


def to_quantity(da: xr.DataArray) -> pint.Quantity:
    """Convert a `xarray.DataArray` to a `pint.Quantity`.

    
    Notes:
        The array's `attrs` metadata mapping must contain a `units` field.
        This function can also be used on coordinate variables.

    Args:
        da: xarray.DataArray instance which will be converted.

    Raises:
        ValueError: If the `xarray.DataArray`'s ``attrs` field does not 
            contain a `units` key.

    Returns:
        The corresponding quantity.
    """
    try:
        units = da.attrs["units"]
    except KeyError as e:
        raise ValueError("this DataArray has no 'units' metadata field") from e
    else:
        return ureg.Quantity(da.values, units)
