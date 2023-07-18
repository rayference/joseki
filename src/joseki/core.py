"""Core module."""
from __future__ import annotations

import datetime
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
from .__version__ import __version__


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


def merge(
    datasets: t.Iterable[xr.Dataset],
    new_title: str | None = None,
) -> xr.Dataset:
    """
    Merge multiple profiles into a single profile.
    
    Args:
        datasets: Iterable of profiles.
        new_title: New title for the merged profile. If `None`, the title of
            the first profile is used.

    Returns:
        Merged profile.
    
    Notes:
        The first profile in the iterable is used as the base profile; when
        variables with the same name are encountered in subsequent profiles,
        the variable from the first profile is used.
    """
    merged = xr.merge(
        datasets,
        compat="override",  # pick variable from first dataset
        combine_attrs="override",  # copy attrs from the first dataset to the result
    )

    # update attributes
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    institutions = set([ds.attrs["institution"] for ds in datasets])
    sources = set([ds.attrs["source"] for ds in datasets])
    references = set([ds.attrs["references"] for ds in datasets])
    urls = set([ds.attrs["url"] for ds in datasets])
    urldates = set([ds.attrs["urldate"] for ds in datasets])
    conventions = set([ds.attrs["Conventions"] for ds in datasets])

    with_profiles = "with profile " if len(datasets) == 2 else "with profiles "
    with_profiles += ", ".join([f"'{ds.title}'" for ds in datasets[1:]])
    merged.attrs["history"] += (
        f"\n{now} - merged profile '{datasets[0].title}' {with_profiles} "
        f"joseki, version {__version__}"
    )

    merged.attrs["institution"] = "\n".join(institutions)
    merged.attrs["source"] = "\n".join(sources)
    merged.attrs["references"] = "\n".join(references)
    merged.attrs["url"] = "\n".join(urls)
    merged.attrs["urldate"] = "\n".join(urldates)
    merged.attrs["Conventions"] = "\n".join(conventions)

    if new_title is not None:  # pragma: no cover
        merged.attrs["title"] = new_title
    else:  # pragma: no cover
        merged.attrs["title"] = datasets[0].title

    return merged


def identifiers() -> t.List[str]:
    """
    List all registered profile identifiers.

    Returns:
        List of all registered profile identifiers.
    """
    return factory.registered_identifiers
