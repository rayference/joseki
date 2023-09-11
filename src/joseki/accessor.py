"""Accessor module."""
from __future__ import annotations

import datetime
import logging
import typing as t

import numpy as np
import pint
import xarray as xr

from .__version__ import __version__
from .constants import MM, AIR_MAIN_CONSTITUENTS_MOLAR_FRACTION
from .profiles.schema import schema
from .profiles.util import molar_mass
from .units import to_quantity, ureg

logger = logging.getLogger(__name__)

def molecular_mass(m: str) -> pint.Quantity:
    """Return the average molecular mass of a molecule.

    Args:
        m: Molecule formula.

    Returns:
        Average molecular mass.
    """
    return MM[m] * ureg("dalton")


def _scaling_factor(
    initial_amount: pint.Quantity,
    target_amount: pint.Quantity,
) -> float:
    """Compute scaling factor given initial and target amounts.

    Args:
        initial_amount: Initial amount.
        target_amount: Target amount.

    Raises:
        ValueError: when the initial amount has a zero magnitude and the target 
          amount has a non-zero magnitude.

    Returns:
        Scaling factor
    """
    if initial_amount.m == 0.0:
        if target_amount.m == 0.0:
            return 0.0
        else:
            raise ValueError(
                f"Cannot compute scaling factor when initial amount has "
                f"magnitude of zero and target amount has a non-zero magnitude "
                f"(got {target_amount})."
            )
    else:
        factor = (target_amount / initial_amount).m_as(ureg.dimensionless)
        return float(factor)


@xr.register_dataset_accessor("joseki")
class JosekiAccessor:  # pragma: no cover
    """Joseki accessor."""

    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    @property
    def molecules(self) -> t.List[str]:
        """Return list of molecules."""
        return [c[2:] for c in self._obj.data_vars if c.startswith("x_")]

    @property
    def column_number_density(
        self,
    ) -> t.Dict[str, pint.Quantity]:
        r"""Compute column number density.

        Returns:
            A mapping of molecule and column number density.

        Notes:
            The column number density is given by:

            $$
            N_{\mathrm{M}} = \int n_{\mathrm{M}}(z) \, \mathrm{d} z
            $$
            
            with

            $$
            n_{\mathrm{M}}(z) = x_{\mathrm{M}}(z) \, n(z)
            $$

            where

            * $z$ is the altitude,
            * $x_{\mathrm{M}}(z)$ is the mole fraction of molecule M
            at altitude $z$,
            * $n(z)$ is the air number density at altitude $z$,
            * $n_{\mathrm{M}}(z)$ is the number density of molecule M at
            altitude $z$.

            The  integration is performed using the trapezoidal rule.
        """
        ds = self._obj
        
        logger.debug(
            "Computing column number density using the trapezoidal rule."
        )

        _column_number_density = {}
        for m in self.molecules:
            integral = (ds[f"x_{m}"] * ds.n).integrate(
                coord="z"
            )  # integrate using the trapezoidal rule
            units = " ".join(
                [ds[var].attrs["units"] for var in [f"x_{m}", "n", "z"]]
            )
            _column_number_density[m] = (
                integral.values * ureg.Unit(units)
            ).to_base_units()

        return _column_number_density

    @property
    def column_mass_density(
        self,
    ) -> t.Dict[str, pint.Quantity]:
        r"""Compute column mass density.

        Returns:
            A mapping of molecule and column mass density.

        Notes:
            The column mass density is given by:

            $$
            \sigma_{\mathrm{M}} = N_{\mathrm{M}} \, m_{\mathrm{M}}
            $$

            where

            * $N_{\mathrm{M}}$ is the column number density of molecule M,
            * $m_{\mathrm{M}}$ is the molecular mass of molecule M.
        """
        _column_number_density = self.column_number_density
        return {
            m: (molecular_mass(m) * _column_number_density[m]).to("kg/m^2")
            for m in self.molecules
        }

    @property
    def number_density_at_sea_level(
        self,
    ) -> t.Dict[str, pint.Quantity]:
        """Compute number density at sea level.

        Returns:
            A mapping of molecule and number density at sea level.
        """
        ds = self._obj
        n = to_quantity(ds.n.isel(z=0))
        return {
            m: (to_quantity(ds[f"x_{m}"].isel(z=0)) * n)
            for m in self.molecules
        }

    @property
    def mass_density_at_sea_level(
        self,
    ) -> t.Dict[str, pint.Quantity]:
        """Compute mass density at sea level.

        Returns:
            A mapping of molecule and mass density at sea level.
        """
        _number_density_at_sea_level = self.number_density_at_sea_level
        return {
            m: (molecular_mass(m) * _number_density_at_sea_level[m]).to("kg/m^3")
            for m in self.molecules
        }

    @property
    def mole_fraction_at_sea_level(
        self,
    ) -> t.Dict[str, pint.Quantity]:
        """Compute mole fraction at sea level.

        Returns:
            A mapping of molecule and mole fraction at sea level.
        """
        ds = self._obj
        return {
            m: to_quantity(ds[f"x_{m}"].isel(z=0)).item()
            for m in self.molecules
        }

    @property
    def mole_fraction(self) -> xr.DataArray:
        """Extract mole fraction and tabulate as a function of (m, z).

        Returns:
            Mole fraction.
        """
        ds = self._obj
        molecules = self.molecules
        concatenated = xr.concat([ds[f"x_{m}"] for m in molecules], dim="m")
        concatenated["m"] = ("m", molecules, {"long_name": "molecule"})
        concatenated.attrs.update(
            {
                "standard_name": "mole_fraction",
                "long_name": "mole fraction",
                "units": "dimensionless",
            }
        )
        concatenated.name = "x"
        return concatenated

    @property
    def mass_fraction(self) -> xr.DataArray:
        """Extract mass fraction and tabulate as a function of (m, z).

        Returns:
            Mass fraction.
        """
        x = self.mole_fraction
        m_air = self.air_molar_mass
        m = molar_mass(molecules=self.molecules)
        y = (x * m / m_air).rename("y")
        y.attrs.update(
            {
                "standard_name": "mass_fraction_in_air",
                "long_name": "mass fraction",
                "units": "kg * kg^-1",
            }
        )
        return y

    @property
    def air_molar_mass(self) -> xr.DataArray:
        r"""
        Compute air molar mass as a function of altitude.

        Returns:
            Air molar mass.

        Notes:
            The air molar mass is given by:

            $$
            M_{\mathrm{air}} = 
            \frac{
                \sum_{\mathrm{M}} x_{\mathrm{M}} \, m_{\mathrm{M}}
            }{
                \sum_{\mathrm{M}} x_{\mathrm{M}}
            }
            $$

            where
            * $x_{\mathrm{M}}$ is the mole fraction of molecule M,
            * $m_{\mathrm{M}}$ is the molar mass of molecule M.

            To compute the air molar mass accurately, the mole fraction of
            molecular nitrogen (N2), molecular oxygen (O2), and argon (Ar) are
            required. If these are not present in the dataset, they are
            computed using the assumption that the mole fraction of these
            molecules are constant with altitude and set to the following
            values:

            * molecular nitrogen (N2): 0.78084
            * molecular oxygen (O2): 0.209476
            * argon (Ar): 0.00934

            are independent of altitude.

            Since nothing garantees that the mole fraction sum is equal to
            one, the air molar mass is computed as the sum of the mole
            fraction weighted molar mass divided by the sum of the mole
            fraction.
        """
        ds = self._obj
        
        # for molar mass computation to be accurate, main air constituents
        # must be present in the dataset
        ds_copy = ds.copy(deep=True)
        for m in AIR_MAIN_CONSTITUENTS_MOLAR_FRACTION:
            if f"x_{m}" not in ds:
                value = AIR_MAIN_CONSTITUENTS_MOLAR_FRACTION[m]
                ds_copy[f"x_{m}"] = ("z", np.full_like(ds.n, value))
                ds_copy[f"x_{m}"].attrs.update({"units": "dimensionless"})
        
        # compute air molar mass
        x = ds_copy.joseki.mole_fraction
        molecules = x.m.values
        mm = xr.DataArray(
            data=np.array([MM[m] for m in molecules]),
            coords={"m": ("m", molecules)},
            attrs={"units": "dimensionless"}
        )

        mm_average = (x * mm).sum(dim="m") / (x.sum(dim="m"))

        mm_average.attrs.update(
            {
                "long_name": "air molar mass",
                "units": "kg/mol",
            }
        )

        return mm_average

    def scaling_factors(
        self, target: t.MutableMapping[str, pint.Quantity | dict | xr.DataArray]
    ) -> t.MutableMapping[str, float]:
        """Compute scaling factor(s) to reach specific target amount(s).

        Args:
            target: Mapping of molecule and target amount.

        Raises:
            ValueError: If a target amount has dimensions that are not supported.

        Returns:
            Mapping of molecule and scaling factors.

        Notes:
            For each molecule in the ``target`` mapping, the target amount is
            interpreted, depending on its dimensions (indicated in square 
            brackets), as:

            * a column number density [`length^-2`],
            * a column mass density [`mass * length^-2`],
            * a number density at sea level [`length^-3`],
            * a mass density at sea level [`mass * length^-3`],
            * a mole fraction at sea level [`dimensionless`]

            The scaling factor is then evaluated as the ratio of the target
            amount with the original amount, for each molecule.

        See Also:
            `rescale`
        """
        compute_initial_amount = {
            "[length]^-2": self.column_number_density,
            "[mass] * [length]^-2": self.column_mass_density,
            "[length]^-3": self.number_density_at_sea_level,
            "[mass] * [length]^-3": self.mass_density_at_sea_level,
            "": self.mole_fraction_at_sea_level,
        }
        factors = {}
        for m, target_amount in target.items():
            target_amount = to_quantity(target_amount)
            initial_amount = None
            for dim in compute_initial_amount.keys():
                if target_amount.check(dim):
                    initial_amount = compute_initial_amount[dim][m]
            if initial_amount is None:
                raise ValueError
            factors[m] = _scaling_factor(
                initial_amount=initial_amount, target_amount=target_amount
            )
        return factors

    def rescale(
        self,
        factors: t.MutableMapping[str, float],
        check_x_sum: bool = False
    ) -> xr.Dataset:
        """Rescale molecules concentration in atmospheric profile.

        Args:
            factors: A mapping of molecule and scaling factor.
            check_x_sum: if True, check that mole fraction sums
                are never larger than one.
        Raises:
            ValueError: if `check_x_sum` is `True` and the 
                dataset is not valid.

        Returns:
            Rescaled dataset (new object).
        """
        ds = self._obj

        # update mole fraction
        x_new = {}
        for m in factors:
            with xr.set_options(keep_attrs=True):
                x_new[f"x_{m}"] = ds[f"x_{m}"] * factors[m]
            
        ds = ds.assign(x_new)

        # validate rescaled dataset
        try:
            ds.joseki.validate(check_x_sum=check_x_sum)
        except ValueError as e:
            raise ValueError("Cannot rescale") from e
        
        # update history attribute
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        for m in factors.keys():
            ds.attrs["history"] += (
                f"\n{now} - rescaled {m}'s mole fraction using a scaling "
                f"factor of {factors[m]:.3f} - joseki, version {__version__}"
            )

        return ds

    def rescale_to(
        self,
        target: t.Mapping[str, pint.Quantity | dict | xr.DataArray],
        check_x_sum: bool = False,
    ) -> xr.Dataset:
        """
        Rescale mole fractions to match target molecular total column 
        densities.

        Args:
            target: Mapping of molecule and target total column density. 
                Total column must be either a column number density 
                [`length^-2`], a column mass density [`mass * length^-2`], a 
                number density at sea level [`length^-3`], a mass density at 
                sea level [`mass * length^-3`], a mole fraction at 
                sea level [`dimensionless`].
            check_x_sum: if True, check that mole fraction sums are never
                larger than one.
        
        Returns:
            Rescaled dataset (new object).    
        """
        return self.rescale(
            factors=self.scaling_factors(target=target),
            check_x_sum=check_x_sum,
        )

    def drop_molecules(
        self,
        molecules: t.List[str],
    ) -> xr.Dataset:
        """Drop molecules from dataset.

        Args:
            molecules: List of molecules to drop.

        Returns:
            Dataset with molecules dropped.
        """
        ds = self._obj

        # update history attribute
        now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        
        ds.attrs["history"] += (
            f"\n{now} - dropped mole fraction data for molecules "
            f"{', '.join(molecules)} - joseki, version {__version__}"
        )

        return ds.drop_vars([f"x_{m}" for m in molecules])

    def validate(
        self,
        check_x_sum: bool = False,
        ret_true_if_valid: bool = False,
    ) -> bool:
        """Validate atmosphere thermophysical profile dataset schema.

        Returns:
            `True` if the dataset complies with the schema, else `False`.
        """
        return schema.validate(
            ds=self._obj,
            check_x_sum=check_x_sum,
            ret_true_if_valid=ret_true_if_valid,
        )

    @property
    def is_valid(self):
        """
        Return `True` if the dataset complies with the schema, else `False`.
        """
        try:
            self.validate(ret_true_if_valid=True)
            return True
        except ValueError:
            return False
