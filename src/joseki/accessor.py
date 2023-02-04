"""Accessor module."""
import datetime
import typing as t

import molmass
import numpy as np
import pint
import xarray as xr

from .__version__ import __version__
from .profiles.schema import schema
from .units import to_quantity, ureg


def molecular_mass(m: str) -> pint.Quantity:
    """Return the average molecular mass of a molecule.

    Args:
        m: Molecule formula.

    Returns:
        Average molecular mass.
    """
    return ureg.Quantity(molmass.Formula(m).mass, "dalton")


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

            n = to_quantity(ds.n)

            _column_number_density = {}
            for m in self.molecules:
                xm = to_quantity(ds[f"x_{m}"])
                _column_number_density[m] = (
                    (xm * n * dz).sum().to_base_units()
                )  # integrate using the centered rectangle rule

            return _column_number_density

        except AttributeError:  # z_bounds attribute does not exist

            _column_number_density = {}
            for m in self.molecules:
                integral = (ds[f"x_{m}"] * ds.n).integrate(
                    coord="z"
                )  # integrate  using the trapeziodal rule
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

    def rescale(self, factors: t.MutableMapping[str, float]) -> None:
        """Rescale molecules concentration in atmospheric profile.

        Args:
            factors: A mapping of molecule and scaling factor.

        Raises:
            ValueError: When the rescaling factors are invalid, i.e. they lead 
                to a profile where the volume fraction sum is larger than 1.
        """
        ds = self._obj

        # update volume fraction in a copy of the dataset
        ds_copy = ds.copy(deep=True)
        for m in self.molecules:
            if m in factors:
                ds_copy[f"x_{m}"] = ds[f"x_{m}"] * factors[m]

        # check that the volume fraction sum is not larger than 1
        vfs = volume_fraction_sum(ds_copy)
        if np.any(vfs.m > 1):
            raise ValueError(
                "The rescaling factors lead to a profile where the volume "
                "fraction sum is larger than 1."
            )
        else:
            # update dataset
            ds.update(ds_copy)

        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for m in factors.keys():
            ds.attrs["history"] += (
                f"\n{now} - rescaled {m}'s volume mixing ratio using a scaling "
                f"factor of {factors[m]:.3f} - joseki, version {__version__}"
            )

        ds.attrs.update(dict(rescaled="True"))

    def validate(self) -> bool:
        """Validate atmosphere thermophysical profile data set schema.
        """
        return schema.validate(ds=self._obj, ret_true_if_valid=True)
