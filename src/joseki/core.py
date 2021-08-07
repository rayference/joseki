"""Core module."""
import datetime
import enum
import pathlib
from typing import Any
from typing import Optional
from typing import Union

import numpy as np
import pint
import xarray as xr
from scipy import interpolate

from .afgl_1986 import Identifier as AFGL1986Identifier
from .afgl_1986 import read as afgl_1986_read
from .rfm import Identifier as RFMIdentifier
from .rfm import read as rfm_read
from .units import ureg
from .util import make_data_set
from .util import to_quantity


class Identifier(enum.Enum):
    """Atmospheric profile data set identifier."""

    AFGL_1986_TROPICAL = "afgl_1986-tropical"
    AFGL_1986_MIDLATITUDE_SUMMER = "afgl_1986-midlatitude_summer"
    AFGL_1986_MIDLATITUDE_WINTER = "afgl_1986-midlatitude_winter"
    AFGL_1986_SUBARCTIC_SUMMER = "afgl_1986-subarctic_summer"
    AFGL_1986_SUBARCTIC_WINTER = "afgl_1986-subarctic_winter"
    AFGL_1986_US_STANDARD = "afgl_1986-us_standard"
    RFM_WIN = "rfm-win"
    RFM_SUM = "rfm-sum"
    RFM_DAY = "rfm-day"
    RFM_NGT = "rfm-ngt"
    RFM_EQU = "rfm-equ"
    RFM_DAY_IMK = "rfm-day_imk"
    RFM_NGT_IMK = "rfm-ngt_imk"
    RFM_SUM_IMK = "rfm-sum_imk"
    RFM_WIN_IMK = "rfm-win_imk"
    RFM_MLS = "rfm-mls"
    RFM_MLW = "rfm-mlw"
    RFM_SAS = "rfm-sas"
    RFM_SAW = "rfm-saw"
    RFM_STD = "rfm-std"
    RFM_TRO = "rfm-tro"


@ureg.wraps(ret=None, args=(None, "km", None, None, None, None), strict=False)
def interp(
    ds: xr.Dataset,
    z_new: Union[pint.Quantity, np.ndarray],  # type: ignore[type-arg]
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
    x_new = ds.x.interp(z=z_new, method=x_interp_method, kwargs=dict(bounds_error=True))

    # Reform data set
    interpolated: xr.Dataset = make_data_set(
        p=p_new,
        t=t_new,
        n=n_new,
        x=x_new.values,
        z=z_new,
        molecules=ds.molecules.values,
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

    Atmosphere cells (or layers) are defined by two consecutive altitude values.
    The layer's center altitude is defined as the average of these two values.
    The pressure, temperature, number density and mixing ratio fields are
    interpolated at these layer' center altitude values.
    In the new atmospheric profile, the 'zn' coordinate is removed, a layer'
    center altitude coordinate 'z' is added and a data variable 'z_bounds'
    indicating the altitude bounds of each layer, is added.


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
    # if the profile is already represented in cells, do nothing
    if ds.z.standard_name == "layer_center_altitude":
        return ds

    z_nodes = to_quantity(ds.z)
    z_centers = (z_nodes[:-1] + z_nodes[1:]) / 2.0
    interpolated: xr.Dataset = interp(
        ds=ds,
        z_new=z_centers,
        p_interp_method=p_interp_method,
        t_interp_method=t_interp_method,
        n_interp_method=n_interp_method,
        x_interp_method=x_interp_method,
    )
    interpolated.z.attrs = dict(
        standard_name="layer_center_altitude",
        long_name="layer center altitude",
        units="km",
    )
    z_bounds = np.array([z_nodes.magnitude[:-1], z_nodes.magnitude[1:]])
    interpolated = interpolated.assign(
        z_bounds=(
            ("zbv", "z"),
            z_bounds,
            dict(
                standard_name="altitude",
                long_name="altitude",
                units="km",
            ),
        )
    )
    interpolated.attrs.update(
        history=interpolated.history + f"\n{datetime.datetime.utcnow()} "
        "- data set coords update - joseki.core.represent_profile_in_cells"
    )

    return interpolated


def make(
    identifier: Identifier,
    altitudes: Optional[pathlib.Path] = None,
    represent_in_cells: bool = False,
    p_interp_method: str = "linear",
    t_interp_method: str = "linear",
    n_interp_method: str = "linear",
    x_interp_method: str = "linear",
    **kwargs: Any,
) -> xr.Dataset:
    """Make atmospheric profile data set.

    This method creates an atmospheric profile data set corresponding to the
    specified identifier.
    It allows to interpolate the atmospheric profile on a different
    level altitude mesh as well as to set the layer center altitude as the data
    set's main coordinate.

    Parameters
    ----------
    identifier: Identifier
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

    kwargs: Any
        Parameters passed to lower-level readers.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    group_name, identifier_name = identifier.value.split("-")
    if group_name == "afgl_1986":
        ds = afgl_1986_read(identifier=AFGL1986Identifier(identifier_name), **kwargs)
    if group_name == "rfm":
        ds = rfm_read(identifier=RFMIdentifier(identifier_name), **kwargs)

    if altitudes is not None:
        ds = interp(
            ds=ds,
            z_new=np.loadtxt(  # type: ignore[no-untyped-call]
                fname=altitudes,
                dtype=float,
                comments="#",
            ),  # type: ignore[no-untyped-call]
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
