"""Module to compute the U.S. Standard Atmosphere 1976.

The U.S. Standard Atmosphere 1976 is a Earth atmosphere thermophysical model 
described in the technical report [NOAA+1976](bibliography.md#NOAA+1976).
"""
import typing as t

import logging

import pint
import ussa1976
import xarray as xr
from attrs import define

from ..units import to_quantity
from .schema import schema, history
from .core import Profile
from .factory import factory


logger = logging.getLogger(__name__)


@factory.register(identifier="ussa_1976")
@define
class USSA1976(Profile):
    """
    Class to compute the U.S. Standard Atmosphere 1976.

    The U.S. Standard Atmosphere 1976 is a Earth atmosphere thermophysical model
    described in the technical report [NOAA+1976](bibliography.md#NOAA+1976).
    """

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        # Since the ussa_1976 model can be evaluated at any altitude, both
        # interp_method and conserve_column are ignored.

        # kwargs are ignored
        if kwargs:
            logger.warning(  # pragma: no cover
                "value of the 'kwargs' parameter will be ignored."
            )

        # variable to compute with the ussa1976 package
        variables = [
            "p",
            "t",
            "n_tot",
            "n",
        ]
        # compute profile
        if z is None:
            logging.debug("Computing profile with ussa1976 package")
            ds = ussa1976.compute(variables=variables)
        else:
            logging.debug("Computing profile with ussa1976 package")
            logging.debug("z=%s", z)
            ds = ussa1976.compute(z=z.m_as("m"), variables=variables)

        # extract data
        coords = {"z": to_quantity(ds["z"]).to("km")}

        data_vars = {}
        data_vars["p"] = to_quantity(ds["p"]).to("Pa")
        data_vars["t"] = to_quantity(ds["t"]).to("K")
        data_vars["n"] = to_quantity(ds["n_tot"]).to("m^-3")

        # compute volume fraction
        for s in ds["s"].values:
            nx = to_quantity(ds["n"].sel(s=s))
            n_tot = to_quantity(ds["n_tot"])
            data_vars[f"x_{s}"] = (nx / n_tot).to("dimensionless")

        attrs = {
            "Conventions": "CF-1.10",
            "title": "U.S. Standard Atmosphere 1976",
            "institution": "NOAA",
            "source": ds.attrs["source"],
            "history": ds.attrs["history"] + "\n" + history(),
            "references": ds.attrs["references"],
            "url": "https://ntrs.nasa.gov/citations/19770009539",
            "urldate": "2022-12-08",
        }

        ds = schema.convert(
            data_vars,
            coords,
            attrs,
        )

        return ds
