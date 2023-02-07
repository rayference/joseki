"""Core module for atmosphere thermophysical profiles.

The `Profile` abstract class defines the interface for atmosphere thermophysical
profiles.
The `interp` function is used to interpolate an atmosphere thermophysical
profile on new altitude values.
The `represent_profile_in_cells` function is used to compute the cells
representation of the atmosphere thermophysical profile.
"""
import logging
import typing as t
from abc import ABC, abstractmethod

import numpy as np
import pint
import xarray as xr
from attrs import define
from scipy import interpolate

from ..__version__ import __version__
from ..units import to_quantity, ureg
from .util import utcnow
from .schema import schema


logger = logging.getLogger(__name__)

DEFAULT_METHOD = {
    "default": "linear",
}


def interp(
    ds: xr.Dataset,
    z_new: pint.Quantity,
    method: t.Dict[str, str] = DEFAULT_METHOD,
) -> xr.Dataset:
    """Interpolate atmospheric profile on new altitudes.

    Args:
        ds: Atmospheric profile to interpolate.
        z_new: Altitudes values at which to interpolate the atmospheric profile.

    method: Mapping of variable and interpolation method.
        If a variable is not in the mapping, the linear interpolation is used.
        By default, linear interpolation is used for all variables.

    Returns:
        Interpolated atmospheric profile.
    """
    z_units = ds.z.attrs["units"]
    z_new_values = z_new.m_as(z_units)

    coords = {"z": z_new.to(z_units)}

    # Interpolate pressure, temperature and density
    data_vars = {}
    for var in ["p", "t", "n"]:
        f = interpolate.interp1d(
            x=ds.z.values,
            y=ds[var].values,
            kind=method.get(var, method["default"]),
            bounds_error=True,
        )
        data_vars[var] = ureg.Quantity(f(z_new_values), ds[var].attrs["units"])

    # Interpolate volume fraction
    for m in ds.joseki.molecules:
        var = f"x_{m}"
        f = interpolate.interp1d(
            x=ds.z.values,
            y=ds[var].values,
            kind=method.get(var, method["default"]),
            bounds_error=True,
        )
        data_vars[var] = ureg.Quantity(f(z_new_values), ds[var].attrs["units"])

    # Attributes
    attrs = ds.attrs
    author = f"joseki, version {__version__}"
    attrs.update(
        {
            "history": f"{utcnow()} - data set interpolation by {author}.",
        }
    )

    # Convert to data set
    logger.debug("convert interpolated data to data set")
    interpolated = schema.convert(
        data_vars=data_vars,
        coords=coords,
        attrs=attrs,
    )

    return interpolated


def represent_profile_in_cells(
    ds: xr.Dataset,
    method: t.Dict[str, str] = DEFAULT_METHOD,
) -> xr.Dataset:
    """Compute the cells representation of the atmosphere thermophysical profile.

    Args:
        ds: Initial atmospheric profile.

        method: Mapping of variable and interpolation method.
            If a variable is not in the mapping, the linear interpolation is used.
            By default, linear interpolation is used for all variables.

    Returns:
        Cells representation of the atmosphere thermophysical profile.

    Notes:
        Atmosphere cells (or layers) are defined by two consecutive altitude 
        values. The layer's center altitude is defined as the arithmetic 
        average of these two values. The pressure, temperature, number density 
        and volume fraction fields are interpolated at these layer' center 
        altitude values. In the new atmospheric profile, the `z` coordinate 
        is updated with layer' center altitude values and a data variable 
        `z_bounds` indicating the altitude bounds of each layer, is added.
        A copy of the data set is returned, the original data set is not 
        modified.
    """
    # if the profile is already represented in cells, do nothing
    if ds.z.standard_name == "layer_center_altitude":
        return ds

    z_nodes = to_quantity(ds.z)
    z_centers = (z_nodes[:-1] + z_nodes[1:]) / 2.0
    interpolated: xr.Dataset = interp(
        ds=ds,
        z_new=z_centers,
        method=method,
    )
    interpolated.z.attrs = dict(
        standard_name="layer_center_altitude",
        long_name="layer center altitude",
        units="km",
    )
    z_bounds = np.stack([z_nodes[:-1], z_nodes[1:]])
    interpolated = interpolated.assign(
        z_bounds=(
            ("zbv", "z"),
            z_bounds.m_as("km"),
            dict(
                standard_name="cell_bound_altitude",
                long_name="cell bound altitude",
                units="km",
            ),
        )
    )
    interpolated.attrs.update(
        history=interpolated.history + f"\n{utcnow()} "
        f"- represent profile on cells - joseki, version {__version__}"
    )

    return interpolated


@define
class Profile(ABC):
    """
    Abstract class for atmosphere thermophysical profiles.
    """

    @abstractmethod
    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        """
        Return the profile as a dataset.

        Args:
            z: Altitude grid.
                If the profile can be evaluated at arbitrary altitudes, this
                parameter is passed to the evaluating method for that profile.
                If the profile is defined on a fixed altitude grid, this parameter
                is used to interpolate the profile on the specified altitude grid.
            interp_method: Interpolation method for each variable.
                If ``None``, the default interpolation method is used.
                Interpolation may be required if the profile is defined on a fixed
                altitude grid, and the altitude grid is not the same as the one
                used to define the profile.
                Interpolation may also not be required, e.g. if the profile is
                defined by analytical function(s) of the altitude variable.
            kwargs: Parameters passed to lower-level methods.

        Returns:
            Atmospheric profile.
        """
        pass  # pragma: no cover
