"""Core module."""
import typing as t
import logging

import pint
import xarray as xr

from .profiles.factory import factory
from .profiles.core import represent_profile_in_cells, DEFAULT_METHOD

logger = logging.getLogger(__name__)


def make(
    identifier: str,
    z: t.Optional[pint.Quantity] = None,
    interp_method: t.Optional[t.Mapping[str, str]] = DEFAULT_METHOD,
    represent_in_cells: bool = False,
    conserve_column: bool = False,
    **kwargs: t.Any,
) -> xr.Dataset:
    """
    Create a profile with the specified identifier.

    Args:
        identifier: Profile identifier.
        z: Altitude values.
        interp_method: Mapping of variable and interpolation method.
        represent_in_cells: If `True`, compute the altitude layer centers and 
            interpolate the profile on the layer centers, and return the 
            interpolated profile.
        conserve_column: If `True`, ensure that column densities are conserved
            during interpolation.
        kwargs: Additional keyword arguments passed to the profile constructor.
    
    Returns:
        Profile as xarray.Dataset.
    """
    logger.info("Creating profile %s", identifier)
    logger.debug("z: %s", z)
    logger.debug("interp_method: %s", interp_method)
    logger.debug("represent_in_cells: %s", represent_in_cells)
    logger.debug("conserve_column: %s", conserve_column)
    logger.debug("kwargs: %s", kwargs)

    profile = factory.create(identifier)

    logger.debug("exporting profile to xarray.Dataset")
    ds = profile.to_dataset(
        z=z,
        interp_method=interp_method,
        conserve_column=conserve_column,
        **kwargs,
    )

    if represent_in_cells:
        ds = represent_profile_in_cells(
            ds,
            method=interp_method,
            conserve_column=conserve_column,
        )
    
    return ds
