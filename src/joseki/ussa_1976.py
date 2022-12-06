"""U.S. Standard Atmosphere 1976 module."""
import typing as t

import pint
import ussa1976
import xarray as xr

from ._version import _version
from .units import to_quantity
from .util import make_data_set


def make(z: t.Optional[pint.Quantity] = None) -> xr.Dataset:  # type: ignore[type-arg]
    """Make atmospheric profile.

    Make the atmospheric profile according to the U.S. Standard Atmosphere
    1976 model :cite:`NASA1976USStandardAtmosphere`.

    Parameters
    ----------
    z: quantity, optional
        Altitude grid.

    Returns
    -------
    dataset
        Atmospheic profile.
    """
    variables = [
        "p",
        "t",
        "n_tot",
        "n",
    ]

    if z is None:
        ds = ussa1976.compute(variables=variables)
    else:
        ds = ussa1976.compute(
            z=z.m_as("m"),
            variables=variables,
        )

    # rename dimension 's' -> 'm'
    ds = ds.rename_dims({"s": "m"})

    # rename variable 's' -> 'm' and update attributes
    ds = ds.rename_vars({"s": "m"})
    ds["m"].attrs.update(
        {
            "long_name": "molecule",
            "standard_name": "gas_molecule",
        }
    )

    # compute volume mixing ratio
    with xr.set_options(keep_attrs=True):  # type: ignore[no-untyped-call]
        x = ds.n / ds.n_tot
        x.attrs.update({"units": "1"})

    # remove variable 'n'
    ds = ds.drop_vars("n")  # pragma: no cover

    # rename variable 'n_tot' -> 'n'
    ds = ds.rename_vars({"n_tot": "n"})

    ds: xr.Dataset = make_data_set(  # type: ignore
        p=to_quantity(ds.p),
        t=to_quantity(ds.t),
        n=to_quantity(ds.n),
        x=to_quantity(x),
        z=to_quantity(ds.z),
        m=ds.m.values.tolist(),
        convention="CF-1.8",
        title="U.S. Standard Atmosphere 1976",
        history=ds.attrs["history"],
        func_name=f"joseki, version {_version}",
        operation="data set formatting",
        source=ds.attrs["source"],
        references=ds.attrs["references"],
        url="https://ntrs.nasa.gov/citations/19770009539",
        url_date="2022-12-05",
    )

    return ds
