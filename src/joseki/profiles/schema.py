"""Dataset schema for atmosphere thermophysical profiles.

The dataset schema defines the variables, coordinates and attributes that are
expected in a dataset representing an atmosphere thermophysical profile.
"""
import logging
import typing as t


from attrs import define
import numpy as np
import numpy.typing as npt
import xarray as xr
import pint

from ..__version__ import __version__
from ..units import ureg
from .util import utcnow

logger = logging.getLogger(__name__)


def history() -> str:
    return f"{utcnow()} dataset formatting by joseki version {__version__}."


def volume_fraction_sum(ds: xr.Dataset) -> pint.Quantity:
    """Compute the sum of volume mixing fractions.

    Args:
        ds: Dataset.

    Returns:
        The sum of volume fractions.
    """
    return (
        sum([ds[c] for c in ds.data_vars if c.startswith("x_")]).values
        * ureg.dimensionless
    )

@define(frozen=True)
class Schema:
    """Dataset schema for atmosphere thermophysical profiles."""

    data_vars = {
        "p": (["z"], npt.NDArray[np.float64], "Pa", "air_pressure"),
        "t": (["z"], npt.NDArray[np.float64], "K", "air_temperature"),
        "n": (["z"], npt.NDArray[np.float64], "m^-3", "air_number_density"),
    }

    coords = {
        "z": ("z", npt.NDArray[np.float64], "km", "altitude"),
    }

    attrs = {
        "Conventions": str,
        "title": str,
        "institution": str,
        "source": str,
        "history": str,
        "references": str,
        "url": str,
        "urldate": str,
    }

    def validate(
        self,
        ds: xr.Dataset,
        check_volume_fraction_sum: bool = False,
        ret_true_if_valid: bool = False,
    ) -> t.Optional[bool]:
        """Validate dataset.

        Args:
            ds: Dataset to validate.
            check_volume_fraction_sum: if True, check that volume fraction sums
                are never larger than one.
            ret_true_if_valid: make this method return True if the dataset is
                valid.

        Raises:
            ValueError: If the dataset does not match the schema.
        
        Returns:
            None or bool: If `ret_true_if_valid` is True, returns True if the 
                dataset is valid, otherwise returns None.
        """
        logger.debug("Validating dataset")

        logger.debug("Checking that all data variables are present")
        for var in self.data_vars:
            if var not in ds.data_vars:
                raise ValueError(f"missing data variable: {var}")  # pragma: no cover

        logger.debug("Checking that 'x_*' data variable(s) are present")
        if not any([name.startswith("x_") for name in ds.data_vars]):
            raise ValueError("missing data variable starting with x_")  # pragma: no cover

        logger.debug("Checking that all coordinates are present")
        for coord in self.coords:
            if coord not in ds.coords:
                raise ValueError(f"missing coordinate: {coord}")  # pragma: no cover

        logger.debug("Checking that all attributes are present")
        for attr in self.attrs:
            if attr not in ds.attrs:
                raise ValueError(f"missing attribute: {attr}")  # pragma: no cover

        logger.debug("Checking that data variables have the correct dimensions")
        for var, (dims, _, _, _) in self.data_vars.items():
            if set(ds[var].dims) != set(dims):
                raise ValueError(  # pragma: no cover
                    f"incorrect dimensions for {var}. Expected {dims}, "
                    f"got {ds[var].dims}"
                )

        logger.debug("Checking that coordinates have the correct dimensions")
        for coord, (dims, _, _, _) in self.coords.items():
            if set(ds[coord].dims) != set(dims):
                raise ValueError(  # pragma: no cover
                    f"incorrect dimensions for {coord}. Expected {dims}, "
                    f"got {ds[coord].dims}"
                )

        logger.debug("Checking that data variables have the correct units")
        for var, (_, _, units, _) in self.data_vars.items():
            if ds[var].units != units:
                raise ValueError(  # pragma: no cover
                    f"incorrect units for {var}. Expected {units}, "
                    f"got {ds[var].units}"
                )

        logger.debug("Checking that coordinates have the correct units")
        for coord, (_, _, units, _) in self.coords.items():
            if ds[coord].units != units:
                raise ValueError(  # pragma: no cover
                    f"incorrect units for {coord}. Expected {units}, "
                    f"got {ds[coord].units}"
                )

        logger.debug("Checking that attributes have the correct types")
        for attr, typ in self.attrs.items():
            if not isinstance(ds.attrs[attr], typ):
                raise ValueError(  # pragma: no cover
                    f"incorrect type for {attr}. Expected {typ}, "
                    f"got {type(ds.attrs[attr])}"
                )

        logger.debug("Checking that data variables have the correct standard names")
        for var, (_, _, _, standard_name) in self.data_vars.items():
            if ds[var].attrs["standard_name"] != standard_name:
                raise ValueError(  # pragma: no cover
                    f"incorrect standard name for {var}. Expected "
                    f"{standard_name}, got "
                    f"{ds[var].attrs['standard_name']}"
                )

        logger.debug(
            "Checking that all x_* data variables have the correct units and "
            "standard names"
        )
        for var in ds.data_vars:
            if var.startswith("x_"):
                m = var[2:]
                if ds[var].attrs["units"] != "dimensionless":
                    raise ValueError(  # pragma: no cover
                        f"incorrect units for {var}. Expected dimensionless, "
                        f"got {ds[var].attrs['units']}"
                    )
                if ds[var].attrs["standard_name"] != f"{m}_volume_fraction":
                    raise ValueError(  # pragma: no cover
                        f"incorrect standard name for {var}. Expected "
                        f"{m}_volume_fraction, got "
                        f"{ds[var].attrs['standard_name']}"
                    )

        if check_volume_fraction_sum:
            logger.debug(
                "Checking that volume fraction sums are never larger than one"
            )
            vfs = volume_fraction_sum(ds)
            if np.any(vfs.m > 1):
                raise ValueError(  # pragma: no cover
                    "The rescaling factors lead to a profile where the volume "
                    "fraction sum is larger than 1."
                )

        logger.info("Dataset is valid")

        if ret_true_if_valid:  # pragma: no cover
            return True

    def convert(
        self,
        data_vars: t.Mapping[str, pint.Quantity],
        coords: t.Mapping[str, pint.Quantity],
        attrs: t.Mapping[str, str],
    ) -> xr.Dataset:
        """Convert input to schema-compliant dataset.
        
        Args:
            data_vars: Mapping of data variable names to quantities.
            coords: Mapping of coordinate names to quantities.
            attrs: Mapping of attribute names to values.
        
        Returns:
            Dataset with schema-compliant data variables, coordinates, and
            attributes.
        """
        logger.debug("converting input to schema-compliant dataset")

        logger.debug("checking that all data variables are present")
        for var in self.data_vars:
            if var not in data_vars:
                raise ValueError(f"missing data variable: {var}")  # pragma: no cover

        logger.debug("checking that there is at least one x_ data variable")
        if not any([name.startswith("x_") for name in data_vars]):
            raise ValueError("missing data variable starting with x_")  # pragma: no cover

        logger.debug("checking that all coordinates are present")
        for coord in self.coords:
            if coord not in coords:
                raise ValueError(f"missing coordinate: {coord}")  # pragma: no cover

        logger.debug("checking that all attributes are present")
        for attr in self.attrs:
            if attr not in attrs:
                raise ValueError(f"missing attribute: {attr}")  # pragma: no cover

        logger.debug("converting data variables to xarray data array tuples")
        for var, (dims, _, units, standard_name) in self.data_vars.items():
            data_vars[var] = (
                dims,
                data_vars[var].m_as(units),
                {
                    "standard_name": standard_name,
                    "long_name": standard_name.replace("_", " "),
                    "units": units,
                },
            )

        logger.debug("converting x_ data variables")
        for var in data_vars:
            if var.startswith("x_"):
                m = var[2:]
                data_vars[var] = (
                    "z",
                    data_vars[var].m_as("dimensionless"),
                    {
                        "standard_name": f"{m}_volume_fraction",
                        "long_name": f"{m} volume fraction",
                        "units": "dimensionless",
                    },
                )

        logger.debug("converting coordinates")
        for attr, (_, _, units, standard_name) in self.coords.items():
            coords[attr] = (
                attr,
                coords[attr].m_as(units),
                {
                    "standard_name": standard_name,
                    "long_name": standard_name.replace("_", " "),
                    "units": units,
                },
            )

        logger.debug("checking that all attributes are present")
        for attr in self.attrs:
            if attr not in attrs:
                raise ValueError(f"missing attribute: {attr}")  # pragma: no cover

        logger.debug("creating dataset")
        return xr.Dataset(
            data_vars=data_vars,
            coords=coords,
            attrs=attrs,
        )


schema = Schema()
