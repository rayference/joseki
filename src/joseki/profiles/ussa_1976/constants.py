"""Constants module.

As much as possible, constants' names are chosen to be as close as possible to
the notations used in :cite:`NASA1976USStandardAtmosphere`.

Notes
-----
Constants' values are evaluated in the following set of units:
* length: meter
* time: second
* mass: kilogram
* temperature: kelvin
* quantity of matter: mole

Note the following derived units:
* 1 Pa = 1 kg * m^-1 * s^-2
* 1 Joule = 1 kg * m^2 * s^-2
"""

import numpy as np
from numpy.typing import NDArray

K = 1.380622e-23
"""Boltzmann constant [J * K^-1]."""

M = {
    "N2": 0.0280134,
    "O2": 0.0319988,
    "Ar": 0.039948,
    "CO2": 0.04400995,
    "Ne": 0.020183,
    "He": 0.0040026,
    "Kr": 0.08380,
    "Xe": 0.13130,
    "CH4": 0.01604303,
    "H2": 0.00201594,
    "O": 0.01599939,
    "H": 0.00100797,
}
"""Molar masses of the individual species [kg * mole^-1]."""

M0 = 0.028964425278793997
"""Sea level mean air molar mass [kg * mole^-1]."""

NA = 6.022169e23
"""Avogadro number [mole^-1]."""

R = 8.31432
"""Universal gas constant [J * K^-1 * mole^-1]."""

G0 = 9.80665
"""Sea level gravity [m / s^-2]."""

H: NDArray[np.float64] = np.array(
    [
        0.0,
        11e3,
        20e3,
        32e3,
        47e3,
        51e3,
        71e3,
        84852.05,
    ]
)
"""Geopotential altitudes of the layers' boundaries (below 86 km) [m]."""

LK: NDArray[np.float64] = np.array(
    [
        -0.0065,
        0.0,
        0.0010,
        0.0028,
        0.0,
        -0.0028,
        -0.0020,
    ]
)
"""Temperature gradients in the seven layers (below 86 km) [K * m^-1]."""

P0 = 101325.0
"""Pressure at sea level [Pa]."""

R0 = 6.356766e6
"""Effective Earth radius [m]."""

T0 = 288.15
"""Temperature at sea level [K]."""

S = 110.4
"""Sutherland constant in eq. 51 of :cite:`NASA1976USStandardAtmosphere` [K]."""

BETA = 1.458e6
""":math:`\\beta` constant in eq. 51 of :cite:`NASA1976USStandardAtmosphere`
[kg * m^-1 * s^-1 * K^-0.5]."""

GAMMA = 1.40
"""Ratio of specific heat of air at constant pressure to the specific heat of
air at constant volume [dimensionless]."""

SIGMA = 3.65e-10
"""Mean effective collision diameter [m]."""

ALPHA = {
    "N2": 0.0,
    "O": 0.0,
    "O2": 0.0,
    "Ar": 0.0,
    "He": -0.4,
    "H": -0.25,
}
"""Thermal diffusion constants above 86 km [dimensionless]."""

A = {
    "O": 6.986e20,
    "O2": 4.863e20,
    "Ar": 4.487e20,
    "He": 1.7e21,
    "H": 3.305e21,
}
"""Thermal diffusion coefficients [m * s^-1]."""
B = {
    "O": 0.75,
    "O2": 0.75,
    "Ar": 0.87,
    "He": 0.691,
    "H": 0.5,
}
"""Thermal diffusion constants [dimensionless]."""

K_7 = 1.2e2
"""Eddy diffusion coefficients [m^2 * s^-1]."""

Q1 = {
    "O": -5.809644e-13,
    "O2": 1.366212e-13,
    "Ar": 9.434079e-14,
    "He": -2.457369e-13,
}
"""Vertical transport constants above 86 km [m^-3]."""

Q2 = {
    "O": -3.416248e-12,  # warning: above 97 km, Q2 = 0 m^-3.
    "O2": 0.0,
    "Ar": 0.0,
    "He": 0.0,
}
"""Vertical transport constants above 86 km [m^-3]."""

U1 = {
    "O": 56.90311e3,
    "O2": 86e3,
    "Ar": 86e3,
    "He": 86e3,
}
"""Vertical transport constants above 86 km [m]."""

U2 = {
    "O": 97e3,
}
"""Vertical transport constants above 86 km [m]."""

W1 = {
    "O": 2.706240e-14,
    "O2": 8.333333e-14,
    "Ar": 8.333333e-14,
    "He": 6.666667e-13,
}
"""Vertical transport constants above 86 km [m^-3]."""

W2 = {
    "O": 5.008765e-13,
}
"""Vertical transport constants above 86 km [m^-3]."""

Z7 = 86e3
"""Top altitude of the 7th layer [m]."""

Z8 = 91e3
"""Top altitude of the 8th layer [m]."""

Z9 = 110e3
"""Top altitude of the 9th layer [m]."""

Z10 = 120e3
"""Top altitude of the 10th layer [m]."""

Z12 = 1000e3
"""Top altitude of the 12nd layer [m]."""

T7 = 186.8673
"""Temperature at altitude :const:`.Z7` [K]."""

T9 = 240.0
"""Temperature at altitude :const:`.Z9` [K]."""

T10 = 360.0
"""Temperature at altitude :const:`.Z10` [K]."""

T11 = 999.2356
"""Temperature at altitude :const:`.Z11` [K]."""

TINF = 1000.0
"""Exospheric temperature [K]."""

LAMBDA = 0.01875e-3
""":math:`\\lambda` constant in eq. 32 of :cite:`NASA1976USStandardAtmosphere`
[m^-1]."""

LK7 = 0.0
"""Temperature gradient in the 8th layer [K * m^-1]."""

LK9 = 12.0e-3
"""Temperature gradient in the 10th layer [K * m^-1]."""

N2_7 = 1.129794e20
"""Molecular nitrogen number density at altitude :const:`.Z7` [m^-3]."""

O_7 = 8.6e16
"""Atomic oxygen number density at altitude :const:`.Z7` [m^-3]."""

O2_7 = 3.030898e19
"""Molecular oxygen number density at altitude :const:`.Z7` [m^-3]."""

AR_7 = 1.351400e18
"""Argon number density at altitude :const:`.Z7` [m^-3]."""

HE_7 = 7.5817e14
"""Helium number density at altitude :const:`.Z7` [m^-3].

Notes
-----
Assumes typo at page 13.
"""

H_11 = 8.0e10
"""Hydrogen number density at altitude :const:`.Z7` [m^-3]."""

PHI = 7.2e11
"""Vertical air particles flux [m^2 * s^-1]."""
