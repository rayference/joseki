"""Accessor module."""
import datetime
import typing as t

import molmass
import numpy as np
import pint
import xarray as xr

from .units import to_quantity
from .units import ureg


def molecular_mass(m: str) -> pint.Quantity:  # type: ignore[type-arg]
    """Return the average molecular mass of a molecule.

    Parameters
    ----------
    m: str
        Molecule formula.

    Returns
    -------
    quantity
        Average molecular mass.
    """
    return ureg.Quantity(float(molmass.Formula(m).mass), "dalton")


def _scaling_factor(
    initial_amount: pint.Quantity, target_amount: pint.Quantity  # type: ignore[type-arg]
) -> float:
    """
    Compute scaling factor given initial and target amounts.

    Parameters
    ----------
    initial_amount: :class:`~pint.Quantity`
        Initial amount.

    target_amount: :class:`~pint.Quantity`
        Target amount.

    Raises
    ------
    ValueError
        when the initial amount has a zero magnitude and the target amount
        has a non-zero magnitude.

    Returns
    -------
    float
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
        return (target_amount / initial_amount).m_as(ureg.dimensionless)  # type: ignore[no-any-return]


@xr.register_dataset_accessor("joseki")  # type: ignore[no-untyped-call]
class JosekiAccessor:  # pragma: no cover
    """Joseki accessor."""

    def __init__(self, xarray_obj):  # type: ignore[no-untyped-def]
        self._obj = xarray_obj

    @property
    def column_number_density(
        self,
    ) -> t.Dict[str, pint.Quantity]:  # type: ignore[type-arg]
        r"""Compute column number density.

        The column number density is given by:

        .. math::
           N_{\mathrm{M}} = \int n_{\mathrm{M}}(z) \, \mathrm{d} z

        with

        .. math::

           n_{\mathrm{M}}(z) = x_{\mathrm{M}}(z) \, n(z)

        where

        * :math:`z` is the altitude,
        * :math:`x_{\mathrm{M}}(z)` is the volume mixing ratio of molecule M
          at altitude :math:`z`,
        * :math:`n(z)` is the air number density at altitude :math:`z`,
        * :math:`n_{\mathrm{M}}(z)` is the number density of molecule M at
          altitude :math:`z`.

        If the dataset has a ``z_bounds`` coordinate, the integral is computed
        using the centered rectangle method, where the ``z`` coordinate
        corresponds to the rectangle centers.

        If the dataset does not have a ``z_bounds`` coordinate, the integration
        is performed using the trapezoidal rule.

        Returns
        -------
        dict
            A mapping of molecule and column number density.
        """
        ds = self._obj
        try:
            with xr.set_options(keep_attrs=True):  # type: ignore[no-untyped-call]
                dz = to_quantity(ds.z_bounds.diff(dim="zbv", n=1).squeeze())

            n = to_quantity(ds.n)

            _column_number_density = {}
            for m in ds.m.values:
                xm = to_quantity(ds.x.sel(m=m))
                _column_number_density[m] = (
                    (xm * n * dz).sum().to_base_units()
                )  # integrate using the centered rectangle rule

            return _column_number_density

        except AttributeError:  # z_bounds attribute does not exist

            _column_number_density = {}
            for m in ds.m.values:
                integral = (ds.x.sel(m=m) * ds.n).integrate(
                    coord="z"
                )  # integrate  using the trapeziodal rule
                units = " ".join([ds[var].attrs["units"] for var in ["x", "n", "z"]])
                _column_number_density[m] = (
                    integral.values * ureg.Unit(units)
                ).to_base_units()

            return _column_number_density

    @property
    def column_mass_density(
        self,
    ) -> t.Dict[str, pint.Quantity]:  # type: ignore[type-arg]
        r"""Compute column mass density.

        The column mass density is given by:

        .. math::

           \sigma_{\mathrm{M}} = N_{\mathrm{M}} \, m_{\mathrm{M}}

        where

        * :math:`N_{\mathrm{M}}` is the column number density of molecule M,
        * :math:`m_{\mathrm{M}}` is the molecular mass of molecule M.

        Returns
        -------
        dict
            A mapping of molecule and column mass density.
        """
        _column_number_density = self.column_number_density
        return {
            m: (molecular_mass(m) * _column_number_density[m]).to("kg/m^2")
            for m in self._obj.m.values
        }

    @property
    def number_density_at_sea_level(
        self,
    ) -> t.Dict[str, pint.Quantity]:  # type: ignore[type-arg]
        """Compute number density at sea level.

        Returns
        -------
        dict:
            A mapping of molecule and number density at sea level.
        """
        ds = self._obj
        n = to_quantity(ds.n.isel(z=0))
        return {m: (to_quantity(ds.x.sel(m=m).isel(z=0)) * n) for m in ds.m.values}

    @property
    def mass_density_at_sea_level(
        self,
    ) -> t.Dict[str, pint.Quantity]:  # type: ignore[type-arg]
        """Compute mass density at sea level.

        Returns
        -------
        dict:
            A mapping of molecule and mass density at sea level.
        """
        _number_density_at_sea_level = self.number_density_at_sea_level
        return {
            m: (molecular_mass(m) * _number_density_at_sea_level[m]).to("kg/m^3")
            for m in self._obj.m.values
        }

    @property
    def volume_mixing_fraction_at_sea_level(self) -> t.Dict[str, pint.Quantity]:  # type: ignore[type-arg]
        """Compute volume mixing fraction at sea level.

        Returns
        -------
        dict:
            A mapping of molecule and volume mixing fraction at sea level.
        """
        ds = self._obj
        return {m: to_quantity(ds.x.sel(m=m).isel(z=0)) for m in ds.m.values}

    def scaling_factors(
        self, target: t.MutableMapping[str, pint.Quantity]  # type: ignore[type-arg]
    ) -> t.MutableMapping[str, float]:
        """
        Compute scaling factor(s) to reach specific target amount(s).

        Seealso
        -------
        :meth:`rescale`

        Parameters
        ----------
        target
            Mapping of molecule and target amount.

        Raises
        ------
        ValueError
            If a target amount has dimensions that are not supported.

        Returns
        -------
        dict
            Mapping of molecule and scaling factors.

        Notes
        -----
        For each molecule in the ``target`` mapping, the target amount is
        interpreted, depending on its dimensions (indicated in square brackets),
        as:

        * a column number density [``length^-2``],
        * a column mass density [``mass * length^-2``],
        * a number densitx at sea level [``length^-3``],
        * a mass density at sea level [``mass * length^-3``],
        * a volume mixing fraction at sea level [``dimensionless``]

        The scaling factor is then evaluated as the ratio of the target amount
        with the original amount, for each molecule.
        """
        compute_initial_amount = {
            "[length]^-2": self.column_number_density,
            "[mass] * [length]^-2": self.column_mass_density,
            "[length]^-3": self.number_density_at_sea_level,
            "[mass] * [length]^-3": self.mass_density_at_sea_level,
            "": self.volume_mixing_fraction_at_sea_level,
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

        Parameters
        ----------
        factors
            A mapping of molecule and scaling factor.

        Raises
        ------
        ValueError
            When the rescaling factors are invalid, i.e. they lead to a profile
            where the volume mixing ratios sum is larger than 1.
        """
        ds = self._obj
        f = xr.DataArray(
            [factors[m] if m in factors else 1.0 for m in ds.m.values],
            coords={"m": ds.m},
            dims="m",
        )
        x_new = ds.x * f

        if np.any(x_new.sum(dim="m") > 1.0):
            raise ValueError(
                "The volume mixing ratio sum is larger than one at at least"
                " one altitude."
            )

        ds["x"].values = x_new

        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for m in factors.keys():
            ds.attrs["history"] += (
                f"\n{now} - rescaled {m}'s volume mixing ratio using a scaling "
                f"factor of {round(factors[m], 3)}"
            )

        ds.attrs.update(dict(rescaled="True"))
