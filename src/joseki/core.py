"""Core module."""
from __future__ import annotations

import logging
import os
import typing as t

import pint
import xarray as xr

from .profiles.factory import factory
from .profiles.core import (
    DEFAULT_METHOD,
    represent_profile_in_cells,
    select_molecules,
)

logger = logging.getLogger(__name__)


def make(
    identifier: str,
    z: pint.Quantity | None = None,
    interp_method: t.Mapping[str, str] | None = DEFAULT_METHOD,
    represent_in_cells: bool = False,
    conserve_column: bool = False,
    molecules: t.List[str] | None = None,
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
        molecules: List of molecules to include in the profile.
        kwargs: Additional keyword arguments passed to the profile constructor.
    
    Returns:
        Profile as xarray.Dataset.
    """
    logger.info("Creating profile %s", identifier)
    logger.debug("z: %s", z)
    logger.debug("interp_method: %s", interp_method)
    logger.debug("represent_in_cells: %s", represent_in_cells)
    logger.debug("conserve_column: %s", conserve_column)
    logger.debug("molecules: %s", molecules)
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
    
    if molecules is not None:
        ds = select_molecules(ds, molecules)
    
    return ds


def open_dataset(path: os.PathLike, *args, **kwargs) -> xr.Dataset:
    """
    Thin wrapper around `xarray.open_dataset`.
    
    Args:
        path: Path to the dataset.

    Returns:
        Profile.
    """
    return xr.open_dataset(path, *args, **kwargs)


def load_dataset(path: os.PathLike, *args, **kwargs) -> xr.Dataset:
    """
    Thin wrapper around `xarray.load_dataset`.
    
    Args:
        path: Path to the dataset.

    Returns:
        Profile.
    """
    return xr.load_dataset(path, *args, **kwargs)


def identifiers() -> t.List[str]:
    """
    List all registered profile identifiers.

    Returns:
        List of all registered profile identifiers.
    """
    return factory.registered_identifiers
