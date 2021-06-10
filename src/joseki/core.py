"""Core module."""
import datetime
import pathlib
from typing import Optional
from typing import Union

import numpy as np
import pint
import xarray as xr
from scipy import interpolate

from .util import to_quantity
from joseki import afgl_1986
from joseki import mipas_rfm
from joseki import ureg
from joseki import util


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
    interpolated: xr.Dataset = util.make_data_set(
        p=p_new,
        t=t_new,
        n=n_new,
        mr=mr_new.values,
        z_level=z_level_new,
        species=ds.species.values,
        func_name="joseki.core.interp",
        operation="data set interpolation",
        **ds.attrs,
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
        z_level.m_as("km"),
        dict(
            standard_name="level_altitude",
            long_name="level altitude",
            units="km",
        ),
    )

    interpolated.attrs.update(
        history=interpolated.history
        + f"\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        "- data set coords update - joseki.core.set_main_coord_to_layer_altitude"
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

    Raises
    ------
    ValueError:
        If atmospheric profile set is unknown.
    """
    group, name = identifier.split("-")
    if group == "afgl_1986":
        ds = afgl_1986.read(name=name)
    elif group == "mipas_rfm":
        ds = mipas_rfm.read(name=name)
    else:
        raise ValueError("Invalid identifier '{identifier}': unknown group '{group}'")

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
