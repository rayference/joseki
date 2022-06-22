"""U.S. Standard Atmosphere 1976 module."""
import datetime
import typing as t

import pint
import ussa1976
import xarray as xr


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
            "standard_name": "molecule",
        }
    )

    # compute volume mixing ratio
    with xr.set_options(keep_attrs=True):  # type: ignore[no-untyped-call]
        x = ds.n / ds.n_tot

    x.attrs.update(
        {
            "long_name": "volume mixing ratio",
            "standard_name": "volume_mixing_ratio",
            "units": "dimensionless",
        }
    )

    # remove variable 'n'
    ds = ds.drop_vars("n")

    # rename variable 'n_tot' -> 'n' and update attributes
    ds = ds.rename_vars({"n_tot": "n"})
    ds["n"].attrs.update(
        {
            "long_name": "air number density",
            "standard_name": "air_number_density",
        }
    )

    # assign volume mixing ratio variable
    ds = ds.assign({"x": x})

    # update data set history
    utcnow = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    history = ds.attrs["history"]
    new_history = f"{utcnow} - data set formatting - joseki"
    ds.attrs.update({"history": f"{history}\n{new_history}"})

    return ds
