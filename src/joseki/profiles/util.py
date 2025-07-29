"""Utility module."""

import datetime
import sys
import typing as t

import numpy as np
import pint
import xarray as xr

from ..constants import MM, K

if sys.version_info[1] < 11:

    def _utcnow():
        return datetime.datetime.utcnow()
else:

    def _utcnow():
        return datetime.datetime.now(datetime.UTC)


def utcnow(isoformat: bool = True):
    result = _utcnow()
    if isoformat:
        return result.replace(microsecond=0).isoformat()
    else:
        return result


def number_density(p: pint.Quantity, t: pint.Quantity) -> pint.Quantity:
    """Compute air number density from air pressure and air temperature.

    Args:
        p: Air pressure.
        t: Air temperature.

    Returns:
        Number density.

    Notes:
        The air number density is computed according to the ideal gas law:

        .. math::

            n = \\frac{p}{k_B T}

        where :math:`p` is the air pressure, :math:`k_B` is the Boltzmann constant,
        and :math:`T` is the air temperature.
    """
    return (p / (K * t)).to_base_units()


def molar_mass(molecules: t.List[str]) -> xr.DataArray:
    return xr.DataArray(
        data=np.array([MM[m] for m in molecules]),
        coords={"m": ("m", molecules)},
        attrs={
            "long_name": "molar mass",
            "standard_name": "molar_mass",
            "units": "g/mol",
        },
    )


def air_molar_mass_from_mass_fraction(y: xr.DataArray) -> xr.DataArray:
    r"""
    Compute the air molar mass from the of air constituents mass fractions.

    Args:
        y: Mass fraction as a function of molecule (`m`) and altitude (`z`).

    Returns:
        Air molar mass as a function of altitude (`z`).

    Notes:
        The air molar mass is computed according to the following equation:

        .. math::

            m_{\mathrm{air}} (z) = \left(
                \sum_{\mathrm{M}} \frac{
                    y_{\mathrm{M}} (z)
                }{
                    m_{\mathrm{M}}
                }
            \right)^{-1}

        where:

        * :math:`y_{\mathrm{M}} (z)` is the mass fraction of molecule M at altitude
          :math:`z`,
        * :math:`m_{\mathrm{M}}` is the molar mass of molecule M.
    """
    # compute molar masses along molecular species
    molecules = y.m.values
    mm = xr.DataArray(
        data=[MM[m] for m in molecules],
        coords={"m": ("m", molecules)},
    )

    # compute air molar mass
    mm_inv = 1 / mm
    weighted_mean_mm_inv = (mm_inv * y).sum(dim="m") / y.sum(dim="m")
    mm_air = 1 / weighted_mean_mm_inv
    mm_air.attrs.update({"units": "g/mol"})
    return mm_air
