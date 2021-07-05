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
from joseki import rfm
from joseki import ureg
from joseki import util


@ureg.wraps(ret=None, args=(None, "km", None, None, None, None), strict=False)
def interp(
    ds: xr.Dataset,
    z_new: Union[pint.Quantity, np.ndarray],
    p_interp_method: str = "linear",
    t_interp_method: str = "linear",
    n_interp_method: str = "linear",
    x_interp_method: str = "linear",
) -> xr.Dataset:
    """Interpolate atmospheric profile on new altitudes.

    Parameters
    ----------
    ds: :class:`~xarray.Dataset`
        Atmospheric profile to interpolate.

    z_new: :class:`~pint.Quantity`, :class:`~numpy.ndarray`
        Altitudes to interpolate the atmospheric profile at [km].

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
        ds.z.values, ds.p.values, kind=p_interp_method, bounds_error=True
    )
    p_new = fp(z_new)

    # Interpolate temperature
    ft = interpolate.interp1d(
        ds.z.values, ds.t.values, kind=t_interp_method, bounds_error=True
    )
    t_new = ft(z_new)

    # Interpolate number density
    fn = interpolate.interp1d(
        ds.z.values, ds.n.values, kind=n_interp_method, bounds_error=True
    )
    n_new = fn(z_new)

    # Interpolate volume mixing ratio
    mr_new = ds.mr.interp(
        z=z_new, method=x_interp_method, kwargs=dict(bounds_error=True)
    )

    # Reform data set
    interpolated: xr.Dataset = util.make_data_set(
        p=p_new,
        t=t_new,
        n=n_new,
        mr=mr_new.values,
        z=z_new,
        species=ds.species.values,
        func_name="joseki.core.interp",
        operation="data set interpolation",
        **ds.attrs,
    )
    return interpolated


def represent_profile_in_cells(
    ds: xr.Dataset,
    p_interp_method: str = "linear",
    t_interp_method: str = "linear",
    n_interp_method: str = "linear",
    x_interp_method: str = "linear",
) -> xr.Dataset:
    """Compute the cells representation of the atmospheric profile.

    The initial altitude values are used to define the altitude bounds of each
    altitude cell.
    The pressure, temperature, number density and mixing ratio fields are then
    interpolated at the altitude cells' centers.
    In the new atmospheric profile, the altitude coordinate provides the
    cells' centers.
    The cells altitude bounds are given by a new 'z_bounds' coordinate.

    Parameters
    ----------
    ds: :class:`~xarray.Dataset`
        Initial atmospheric profile.

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
        Cells representation of the atmospheric profile.
    """
    z = to_quantity(ds.z)
    z_center = (z[:-1] + z[1:]) / 2.0
    interpolated: xr.Dataset = interp(
        ds=ds,
        z_new=z_center,
        p_interp_method=p_interp_method,
        t_interp_method=t_interp_method,
        n_interp_method=n_interp_method,
        x_interp_method=x_interp_method,
    )
    interpolated.z.attrs.update(
        dict(
            bounds="altitude_bounds",
        )
    )
    z_bounds = np.array([z.magnitude[:-1], z.magnitude[1:]]).swapaxes(0, 1)
    interpolated.coords["z_bounds"] = (("z", "zbv"), z_bounds)
    interpolated.attrs.update(
        history=interpolated.history + f"\n{datetime.datetime.utcnow()} "
        "- data set coords update - joseki.core.set_main_coord_to_layer_altitude"
    )

    return interpolated


def make(
    identifier: str,
    altitudes: Optional[pathlib.Path] = None,
    represent_in_cells: bool = False,
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

    altitudes: pathlib.Path
        Altitudes data file.
        If ``None``, the original atmospheric profile altitudes are used.

    represent_in_cells: bool
        If ``True``, compute the cells representation of the atmospheric profile.

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
    elif group == "rfm":
        ds = rfm.read(name=name)
    else:
        raise ValueError("Invalid identifier '{identifier}': unknown group '{group}'")

    if altitudes is not None:
        z_level = np.loadtxt(fname=altitudes, dtype=float, comments="#")
        ds = interp(
            ds=ds,
            z_new=z_level,
            p_interp_method=p_interp_method,
            t_interp_method=t_interp_method,
            n_interp_method=n_interp_method,
            x_interp_method=x_interp_method,
        )

    if represent_in_cells:
        ds = represent_profile_in_cells(
            ds=ds,
            p_interp_method=p_interp_method,
            t_interp_method=t_interp_method,
            n_interp_method=n_interp_method,
            x_interp_method=x_interp_method,
        )

    return ds
