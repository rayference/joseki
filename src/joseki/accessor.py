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
        """Compute mass mass density at sea level.

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
