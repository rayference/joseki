"""Core module for atmosphere thermophysical profiles.

The `Profile` abstract class defines the interface for atmosphere thermophysical
profiles.
The `interp` function is used to interpolate an atmosphere thermophysical
profile on new altitude values.
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
from .schema import schema
from .util import utcnow

logger = logging.getLogger(__name__)

DEFAULT_METHOD = {
    "default": "linear",
}

DEFAULT_OPTIONS = {
    #"num": 100,
    #"zstep": 0.1 * ureg.km,
    "zstep": "auto",
}

def rescale_to_column(reference: xr.Dataset, ds: xr.Dataset) -> xr.Dataset:
    """Rescale mole fraction to ensure that column densities are conserved.
    
    Args:
        reference: Reference profile.
        ds: Profile to rescale.
    
    Returns:
        Rescaled profile.
    """
    desired = reference.joseki.column_number_density
    actual = ds.joseki.column_number_density
    factors = {}
    for m in reference.joseki.molecules:
        if desired[m].m == 0.0:
            factors[m] = 0.0
        elif actual[m].m == 0.0:
            msg = (
                f"Actual column number density of {m} is zero but the reference "
                f"column number density is not ({desired[m]:~P}): rescaling "
                f"is impossible."
            )
            logger.critical(msg)
            raise ValueError(msg)
        else:
            factors[m] = (desired[m] / actual[m]).m_as("dimensionless")

    return ds.joseki.rescale(factors=factors)


def interp(
    ds: xr.Dataset,
    z_new: pint.Quantity,
    method: t.Dict[str, str] = DEFAULT_METHOD,
    conserve_column: bool = False,
    **kwargs: t.Any,
) -> xr.Dataset:
    """Interpolate atmospheric profile on new altitudes.

    Args:
        ds: Atmospheric profile to interpolate.
        z_new: Altitudes values at which to interpolate the atmospheric profile.
        method: Mapping of variable and interpolation method.
            If a variable is not in the mapping, the linear interpolation is used.
            By default, linear interpolation is used for all variables.
        conserve_column: If True, ensure that column densities are conserved.
        kwargs: Parameters passed to `scipy.interpolate.interp1d` (except 
            'kind' and 'bounds_error').

    Returns:
        Interpolated atmospheric profile.
    """
    # sort altitude values
    z_new = np.sort(z_new)

    z_units = ds.z.attrs["units"]
    z_new_values = z_new.m_as(z_units)

    coords = {"z": z_new.to(z_units)}

    # kwargs cannot contain 'kind' and 'bounds_error'
    kwargs.pop("kind", None)
    kwargs.pop("bounds_error", None)

    try:
        if kwargs["fill_value"] == "extrapolate":  # pragma: no cover
            bounds_error = None
    except KeyError:
        bounds_error = True


    # Interpolate pressure, temperature and density
    data_vars = {}
    for var in ["p", "t", "n"]:
        f = interpolate.interp1d(
            x=ds.z.values,
            y=ds[var].values,
            kind=method.get(var, method["default"]),
            bounds_error=bounds_error,
            **kwargs,
        )
        data_vars[var] = ureg.Quantity(f(z_new_values), ds[var].attrs["units"])

    # Interpolate mole fraction
    for m in ds.joseki.molecules:
        var = f"x_{m}"
        f = interpolate.interp1d(
            x=ds.z.values,
            y=ds[var].values,
            kind=method.get(var, method["default"]),
            bounds_error=bounds_error,
            **kwargs,
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


def extrapolate(
    ds: xr.Dataset,
    z_extra: pint.Quantity,
    direction: str,
    method: t.Dict[str, str] = DEFAULT_METHOD,
    conserve_column: bool = False,
) -> xr.Dataset:
    """
    Extrapolate an atmospheric profile to new altitude(s).

    Args:
        ds: Initial atmospheric profile.
        z_extra: Altitude(s) to extrapolate to.
        direction: Direction of the extrapolation, either "up" or "down".
        method: Mapping of variable and interpolation method.
            If a variable is not in the mapping, the linear interpolation is used.
            By default, linear interpolation is used for all variables.
        conserve_column: If True, ensure that column densities are conserved.
    
    Raises:
        ValueError: If the extrapolation direction is not "up" or "down".

    Returns:
        Extrapolated atmospheric profile.
    """
    if direction not in ["up", "down"]:
        msg = (
            f"Extrapolation direction must be either 'up' or 'down', got "
            f"{direction}."
        )
        logger.critical(msg)
        raise ValueError(msg)

    z = to_quantity(ds.z)

    if direction == "down" and np.any(z_extra >= z.min()):
        msg = (
            f"Cannot extrapolate down to {z_extra:~P}, "
            f"minimum altitude is {z.min():~P}."
        )
        logger.critical(msg)
        raise ValueError(msg)
    
    elif direction == "up" and np.any(z_extra <= z.max()):
        msg = (
            f"Cannot extrapolate up to {z_extra:~P}, "
            f"maximum altitude is {z.max():~P}."
        )
        logger.critical(msg)
        raise ValueError(msg)
    
    else:
        extrapolated = interp(
            ds=ds,
            z_new=np.concatenate([np.atleast_1d(z_extra), z]),
            method=method,
            conserve_column=conserve_column,
            fill_value="extrapolate",
        )
        extrapolated.attrs.update(
            history=extrapolated.history + f"\n{utcnow()} "
            f"- extrapolate - joseki, version {__version__}"
        )
        return extrapolated


def regularize(
    ds: xr.Dataset,
    method: t.Dict[str, str] = DEFAULT_METHOD,
    conserve_column: bool = False,
    options: t.Dict[str, t.Union[int, str, pint.Quantity]] = DEFAULT_OPTIONS,
    **kwargs: t.Any,
) -> xr.Dataset:
    """Regularize the profile's altitude grid.
    
    Args:
        ds: Initial atmospheric profile.
        method: Mapping of variable and interpolation method.
            If a variable is not in the mapping, the linear interpolation is used.
            By default, linear interpolation is used for all variables.
        conserve_column: If True, ensure that column densities are conserved.
        options: Options for the regularization.
            Mapping with possible keys:
                - "num": Number of points in the new altitude grid.
                - "zstep": Altitude step in the new altitude grid.
                    If "auto", the minimum altitude step is used.
        kwargs: Keyword arguments passed to the interpolation function.

    Returns:
        Regularized atmospheric profile.
    """
    z = to_quantity(ds.z)
    if options.get("num", None):
        z_new = np.linspace(
            z.min(),
            z.max(),
            options["num"],
        )
    elif options.get("zstep", None):
        zstep = options["zstep"]
        zunits = z.units
        if isinstance(zstep, ureg.Quantity):
            pass
        elif isinstance(zstep, str):
            if zstep == "auto":
                zstep = np.diff(z).min()
            else:
                raise ValueError(f"Invalid zstep value: {zstep}")
        else:
            raise ValueError(f"Invalid zstep value: {zstep}")
        z_new = np.arange(
            z.min().m_as(zunits),
            z.max().m_as(zunits),
            zstep.m_as(zunits),
        ) * zunits

    else:
        raise ValueError("options must contain either 'num' or 'zstep' key.")

    return interp(
        ds=ds,
        z_new=z_new,
        method=method,
        conserve_column=conserve_column,
        **kwargs,
    )


def select_molecules(
    ds: xr.Dataset,
    molecules: t.List[str],
) -> xr.Dataset:
    """
    Select specified molecules in the profile.

    Args:
        ds: Initial atmospheric profile.
        molecules: List of molecules to select.
    
    Returns:
        Atmospheric profile with exactly the specified molecules.
    """
    drop_molecules = [m for m in ds.joseki.molecules if m not in molecules]
    ds_dropped = ds.joseki.drop_molecules(drop_molecules)

    if all([m in ds_dropped.joseki.molecules for m in molecules]):
        return ds_dropped
    else:
        raise ValueError(
            f"Could not select molecules {molecules}, "
            f"available molecules are {ds.joseki.molecules}."
        )

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
