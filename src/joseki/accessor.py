"""Accessor module."""
import datetime
import logging
import typing as t

import pint
import xarray as xr

from .__version__ import __version__
from .profiles.schema import schema
from .units import to_quantity, ureg


logger = logging.getLogger(__name__)

# average molecular masses [dalton]
# (computed with molmass: https://pypi.org/project/molmass/)
MM = {
    "Ar": 39.948,
    "CCl2F2": 120.913,
    "CCl3F": 137.368,
    "CCl4": 153.822,
    "CF4": 88.004,
    "CHClF2": 86.468,
    "CH3Cl": 50.487,
    "CH4": 16.043,
    "CO": 28.010,
    "COF2": 66.007,
    "CO2": 44.010,
    "C2H2": 26.037,
    "C2H6": 30.069,
    "ClO": 51.452,
    "ClONO2": 97.458,
    "H": 1.008,
    "H2": 2.016,
    "HBr": 80.911,
    "HCN": 27.025,
    "HCl": 36.461,
    "He": 4.003,
    "HF": 20.006,
    "HI": 127.912,
    "HOCl": 52.460,
    "HNO3": 63.013,
    "HNO4": 79.012,
    "H2O": 18.015,
    "H2O2": 34.015,
    "H2CO": 30.026,
    "Kr": 83.798,
    "NH3": 17.031,
    "Ne": 20.180,
    "NO": 30.006,
    "NO2": 46.006,
    "N2": 28.013,
    "N2O": 44.013,
    "N2O5": 108.010,
    "OH": 17.007,
    "OCS": 60.075,
    "O": 15.999,
    "O2": 31.999,
    "O3": 47.998,
    "PH3": 33.998,
    "SF6": 146.055,
    "SO2": 64.064,
    "Xe": 131.293,
}

def molecular_mass(m: str) -> pint.Quantity:
    """Return the average molecular mass of a molecule.

    Args:
        m: Molecule formula.

    Returns:
        Average molecular mass.
    """
    return MM[m] * ureg("dalton")


def _scaling_factor(
    initial_amount: pint.Quantity,  # type: ignore[type-arg]
    target_amount: pint.Quantity,  # type: ignore[type-arg]
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
            * $x_{\mathrm{M}}(z)$ is the volume mixing ratio of molecule M
            at altitude $z$,
            * $n(z)$ is the air number density at altitude $z$,
            * $n_{\mathrm{M}}(z)$ is the number density of molecule M at
            altitude $z$.

            If the dataset has a `z_bounds` coordinate, the integral is computed
            using the centered rectangle method, where the `z` coordinate
            corresponds to the rectangle centers.

            If the dataset does not have a `z_bounds` coordinate, the 
            integration is performed using the trapezoidal rule.
        """
        ds = self._obj
        try:
            with xr.set_options(keep_attrs=True):
                dz = to_quantity(ds.z_bounds.diff(dim="zbv", n=1).squeeze())
            
            logger.debug(
                "Computing column number density using the centered rectangle "
                "rule."
            )

            n = to_quantity(ds.n)

            _column_number_density = {}
            for m in self.molecules:
                xm = to_quantity(ds[f"x_{m}"])
                _column_number_density[m] = (
                    (xm * n * dz).sum().to_base_units()
                )  # integrate using the centered rectangle rule

            return _column_number_density

        except AttributeError:  # z_bounds attribute does not exist

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
        return {m: (to_quantity(ds[f"x_{m}"].isel(z=0)) * n) for m in self.molecules}

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
    def volume_fraction_at_sea_level(
        self,
    ) -> t.Dict[str, pint.Quantity]:
        """Compute volume fraction at sea level.

        Returns:
            A mapping of molecule and volume mixing fraction at sea level.
        """
        ds = self._obj
        return {m: to_quantity(ds[f"x_{m}"].isel(z=0)) for m in self.molecules}

    @property
    def volume_fraction(self) -> xr.DataArray:
        """Extract volume fraction and tabulate as a function of (m, z).

        Returns:
            Volume fraction.
        """
        ds = self._obj
        molecules = self.molecules
        concatenated = xr.concat([ds[f"x_{m}"] for m in molecules], dim="m")
        concatenated["m"] = ("m", molecules, {"long_name": "molecule"})
        concatenated.attrs.update(
            {
                "standard_name": "volume_fraction",
                "long_name": "volume fraction",
                "units": "dimensionless",
            }
        )
        concatenated.name = "x"
        return concatenated

    def scaling_factors(
        self, target: t.MutableMapping[str, pint.Quantity]
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
            * a number densitx at sea level [`length^-3`],
            * a mass density at sea level [`mass * length^-3`],
            * a volume mixing fraction at sea level [`dimensionless`]

            The scaling factor is then evaluated as the ratio of the target amount
            with the original amount, for each molecule.

        See Also:
            `rescale`
        """
        compute_initial_amount = {
            "[length]^-2": self.column_number_density,
            "[mass] * [length]^-2": self.column_mass_density,
            "[length]^-3": self.number_density_at_sea_level,
            "[mass] * [length]^-3": self.mass_density_at_sea_level,
            "": self.volume_fraction_at_sea_level,
        }
        factors = {}
        for m, target_amount in target.items():
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
        check_volume_fraction_sum: bool = False
    ) -> xr.Dataset:
        """Rescale molecules concentration in atmospheric profile.

        Args:
            factors: A mapping of molecule and scaling factor.
            check_volume_fraction_sum: if True, check that volume fraction sums
                are never larger than one.
        Raises:
            ValueError: if check_volume_fraction_sum is `True` and the 
                dataset is not valid.

        Returns:
            Rescaled dataset (new object).
        """
        ds = self._obj

        # update volume fraction
        x_new = {}
        for m in factors:
            with xr.set_options(keep_attrs=True):
                x_new[f"x_{m}"] = ds[f"x_{m}"] * factors[m]
            
        ds = ds.assign(x_new)

        # validate rescaled dataset
        try:
            ds.joseki.validate(check_volume_fraction_sum=check_volume_fraction_sum)
        except ValueError as e:
            raise ValueError("Cannot rescale") from e
        
        # update history attribute
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for m in factors.keys():
            ds.attrs["history"] += (
                f"\n{now} - rescaled {m}'s volume mixing ratio using a scaling "
                f"factor of {factors[m]:.3f} - joseki, version {__version__}"
            )

        return ds

    def validate(
        self,
        check_volume_fraction_sum: bool = False,
        ret_true_if_valid: bool = False,
    ) -> bool:
        """Validate atmosphere thermophysical profile dataset schema.

        Returns:
            `True` if the dataset complies with the schema, else `False`.
        """
        return schema.validate(
            ds=self._obj,
            check_volume_fraction_sum=check_volume_fraction_sum,
            ret_true_if_valid=ret_true_if_valid,
        )

    @property
    def is_valid(self):
        return self.validate(ret_true_if_valid=True)
