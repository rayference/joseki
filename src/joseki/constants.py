from .units import ureg
from ussa1976.constants import F

# Boltzmann constant (according to SciPy v1.10.1 Manual)
K = 1.380649e-23 * ureg.joule /  ureg.kelvin

# air main constituents molar fractions (values according to US Standard 
# Atmosphere 1976)
AIR_MAIN_CONSTITUENTS_MOLAR_FRACTION = {
    m: F[m] for m in ["N2", "O2", "Ar"]
}

# average molecular masses [dalton]
# (computed with molmass: https://pypi.org/project/molmass/)
MM = {
    "Ar": 39.948,
    "CCl2F2": 120.913,
    "CCl3F": 137.368,
    "CCl4": 153.822,
    "CF4": 88.004,
    "CHClF2": 86.468,
    "CH3Br": 94.938,
    "CH3CN": 41.052,
    "CH3Cl": 50.487,
    "CH3F": 34.033,
    "CH3I": 141.939,
    "CH3OH": 32.042,
    "CH4": 16.043,
    "CO": 28.010,
    "COF2": 66.007,
    "CO2": 44.010,
    "COCl2": 98.916,
    "CS": 44.076,
    "CS2": 76.14,
    "C2H2": 26.037,
    "C2H4": 28.053,
    "C2H6": 30.069,
    "C2N2": 52.035,
    "C4H2": 50.059,
    "ClO": 51.452,
    "ClONO2": 97.458,
    "GeH4": 76.662,
    "H": 1.008,
    "H2": 2.016,
    "HBr": 80.911,
    "HCN": 27.025,
    "HCOOH": 46.025,
    "HC3N": 51.047,
    "HCl": 36.461,
    "He": 4.003,
    "HF": 20.006,
    "HI": 127.912,
    "HOBr": 96.911,
    "HOCl": 52.460,
    "HO2": 33.007,
    "HNO3": 63.013,
    "HNO4": 79.012,
    "H2O": 18.015,
    "H2O2": 34.015,
    "H2CO": 30.026,
    "H2S": 34.081,
    "Kr": 83.798,
    "NF3": 71.002,
    "NH3": 17.031,
    "Ne": 20.180,
    "NO": 30.006,
    "NO+": 30.006,
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
    "SO": 48.064,
    "SO2": 64.064,
    "SO3": 80.063,
    "Xe": 131.293,
}