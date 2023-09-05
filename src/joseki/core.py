"""Core module."""
from __future__ import annotations

import datetime
import logging
import os
import typing as t

import numpy as np
import pint
import xarray as xr

from .profiles.factory import factory
from .profiles.core import (
    DEFAULT_METHOD,
    select_molecules,
)
from .profiles.core import regularize as _regularize
from .__version__ import __version__
from .units import to_quantity


logger = logging.getLogger(__name__)


def make(
    identifier: str,
    z: pint.Quantity | dict | xr.DataArray | None = None,
    interp_method: t.Mapping[str, str] | None = DEFAULT_METHOD,
    conserve_column: bool = False,
    molecules: t.List[str] | None = None,
    regularize: bool | dict | None = None,
    rescale_to: dict | None = None,
    check_x_sum: bool = False,
    **kwargs: t.Any,
) -> xr.Dataset:
    """
    Create a profile with the specified identifier.

    Args:
        identifier: Profile identifier.
        z: Altitude values.
        interp_method: Mapping of variable and interpolation method.
        conserve_column: If `True`, ensure that column densities are conserved
            during interpolation.
        molecules: List of molecules to include in the profile.
        regularize: Regularize the altitude grid with specified options which
            are passed to 
            [regularize](reference.md#src.joseki.profiles.core.regularize).
        rescale_to: Rescale molecular concentrations to the specified target 
            values which are passed to 
            [rescale_to](reference.md#src.joseki.accessor.JosekiAccessor.rescale_to).  
        check_x_sum: If `True`, check that the mole fraction sums are less or 
            equal to 1.
        kwargs: Additional keyword arguments passed to the profile constructor.
    
    Returns:
        Profile as xarray.Dataset.
    
    See Also:
        [regularize](reference.md#src.joseki.profiles.core.regularize)
        [rescale_to](reference.md#src.joseki.accessor.JosekiAccessor.rescale_to)
    """
    logger.info("Creating profile %s", identifier)
    logger.debug("z: %s", z)
    logger.debug("interp_method: %s", interp_method)
    logger.debug("conserve_column: %s", conserve_column)
    logger.debug("molecules: %s", molecules)
    logger.debug("regularize: %s", regularize)
    logger.debug("rescale_to: %s", rescale_to)
    logger.debug("kwargs: %s", kwargs)
    
    # Convert z to pint.Quantity
    z = to_quantity(z) if z is not None else None

    profile = factory.create(identifier)

    logger.debug("exporting profile to xarray.Dataset")
    ds = profile.to_dataset(
        z=z,
        interp_method=interp_method,
        conserve_column=conserve_column,
        **kwargs,
    )
    
    # Molecules selection
    if molecules is not None:
        ds = select_molecules(ds, molecules)
    
    # Altitude grid regularization
    if regularize:
        z = to_quantity(ds.z)
        default_num = int((z.max() - z.min()) // np.diff(z).min()) + 1
        if isinstance(regularize, bool):
            regularize = {}
        ds = _regularize(
            ds=ds,
            method=regularize.get("method", DEFAULT_METHOD),
            conserve_column=regularize.get("conserve_column", False),
            options=regularize.get('options', {"num": default_num}),
        )
    
    # Molecular concentration rescaling
    if rescale_to:
        ds = ds.joseki.rescale_to(
            target=rescale_to,
            check_x_sum=check_x_sum,
        )
    
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
