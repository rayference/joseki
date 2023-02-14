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


def rescale_to_column(reference: xr.Dataset, ds: xr.Dataset) -> xr.Dataset:
    """Rescale volume fraction to ensure that column densities are conserved.
    
    Args:
        reference: Reference profile.
        ds: Profile to rescale.
    
    Returns:
        Rescaled profile.
    """
    desired = reference.joseki.column_number_density
    actual = ds.joseki.column_number_density
    rescaled = ds.joseki.rescale(
        factors= {
            m: (desired[m] / actual[m]).m_as("dimensionless")
            for m in reference.joseki.molecules
        }
    )
    return rescaled


def interp(
    ds: xr.Dataset,
    z_new: pint.Quantity,
    method: t.Dict[str, str] = DEFAULT_METHOD,
    conserve_column: bool = False,
) -> xr.Dataset:
    """Interpolate atmospheric profile on new altitudes.

    Args:
        ds: Atmospheric profile to interpolate.
        z_new: Altitudes values at which to interpolate the atmospheric profile.
        method: Mapping of variable and interpolation method.
            If a variable is not in the mapping, the linear interpolation is used.
            By default, linear interpolation is used for all variables.
        conserve_column: If True, ensure that column densities are conserved.

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
            "history": f"{utcnow()} - dataset interpolation by {author}.",
        }
    )

    # Convert to dataset
    logger.debug("convert interpolated data to dataset")
    interpolated = schema.convert(
        data_vars=data_vars,
        coords=coords,
        attrs=attrs,
    )
    
    # Compute scaling factors to conserve column densities
    if conserve_column:
        return rescale_to_column(reference=ds, ds=interpolated)

    return interpolated


def represent_profile_in_cells(
    ds: xr.Dataset,
    method: t.Dict[str, str] = DEFAULT_METHOD,
    conserve_column: bool = False,
) -> xr.Dataset:
    """Compute the cells representation of the atmosphere thermophysical profile.

    Args:
        ds: Initial atmospheric profile.
        method: Mapping of variable and interpolation method.
            If a variable is not in the mapping, the linear interpolation is used.
            By default, linear interpolation is used for all variables.
        conserve_column: If True, ensure that column densities are conserved.

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
        A copy of the dataset is returned, the original dataset is not 
        modified.
    """
    # if the profile is already represented in cells, do nothing
    if ds.z.standard_name == "layer_center_altitude":
        return ds

    z_nodes = to_quantity(ds.z)
    z_centers = (z_nodes[:-1] + z_nodes[1:]) / 2.0

    logger.debug("O3 column amount: %s", ds.joseki.column_number_density["O3"].to("dobson_unit"))
    interpolated = interp(
        ds=ds,
        z_new=z_centers,
        method=method,
        conserve_column=False,  # we rescale later
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
    logger.debug("O3 column amount: %s", interpolated.joseki.column_number_density["O3"].to("dobson_unit"))
    interpolated.attrs.update(
        history=interpolated.history + f"\n{utcnow()} "
        f"- represent profile on cells - joseki, version {__version__}"
    )

    if conserve_column:
        return rescale_to_column(reference=ds, ds=interpolated)
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
        conserve_column: bool = False,
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
            conserve_column: If `True`, ensure that column densities are conserved
                during interpolation.
            kwargs: Parameters passed to lower-level methods.

        Returns:
            Atmospheric profile.
        """
        pass  # pragma: no cover
