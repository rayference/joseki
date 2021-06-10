"""Module to read MIPAS atmospheric profiles.

Data are provided by RFM (http://eodg.atm.ox.ac.uk/RFM/).
"""
import importlib.resources as pkg_resources
from typing import Dict
from typing import List
from typing import Tuple

import numpy as np
import requests
import xarray as xr
from scipy.constants import physical_constants

from .data import rfm
from joseki import ureg
from joseki.core import make_data_set

# Boltzmann constant
K = ureg.Quantity(*physical_constants["Boltzmann constant"][:2])


def _parse_units(s: str) -> str:
    """Parse units."""
    if s.startswith("[") and s.endswith("]"):
        units = s[1:-1]
        if units == "mb":
            return "millibar"
        else:
            return units
    else:
        raise ValueError(f"Cannot parse units '{s}'")


def _parse_var_name(n: str) -> str:
    """Parse variable name."""
    translate = {"HGT": "z_level", "PRE": "p", "TEM": "t"}
    if n in translate.keys():
        return translate[n]
    else:
        return n


def _parse_var_line(s: str) -> Tuple[str, str]:
    """Parse a line with the declaration of a variable and its units."""
    parts = s[1:].strip().split()
    if len(parts) == 2:
        var_name, units_s = parts
    elif len(parts) == 3:
        var_name, _, units_s = parts
    else:
        raise ValueError(f"Invalid line format: {s}")
    var = _parse_var_name(var_name)
    units = _parse_units(units_s)
    return var, units


def _parse_values_line(s: str) -> List[str]:
    """Parse a line with numeric values."""
    if "," in s:  # delimiter is comma and whitespace combined
        s_strip = s.strip()
        if s_strip[-1] == ",":
            s_strip = s_strip[:-1]
        return [x.strip() for x in s_strip.split(",")]
    else:  # delimiter is whitespace
        return s.split()


def _parse_content(lines: List[str]) -> Dict[str, ureg.Quantity]:
    """Parse lines."""
    iterator = iter(lines)
    line = next(iterator)

    quantities: Dict[str, ureg.Quantity] = {}

    def _add_to_quantities(quantity: ureg.Quantity, name: str) -> None:
        if quantity.units == "ppmv":
            quantities[name] = quantity.to("dimensionless")
        else:
            quantities[name] = quantity

    var: str = ""
    units: str = ""
    values: List[str] = []
    while line != "*END":
        if line.startswith("!"):
            pass  # this is a comment, ignore the line
        elif line.startswith("*"):
            # convert previously read values (if any) and units to quantity
            if len(values) > 0:
                quantity = ureg.Quantity(np.array(values, dtype=float), units)
                _add_to_quantities(quantity=quantity, name=var)

            # this is a variable line, parse variable name and units
            var, units = _parse_var_line(line)

            # following lines are the variables values so prepare a variable
            # to store the values
            values = []
        else:
            if "!" in line:
                # this the line with the number of profile levels, ignore it
                pass
            else:
                # this line contains variable values
                values += _parse_values_line(line)
        line = next(iterator)

    # include last array of values before the '*END' line
    quantity = ureg.Quantity(np.array(values, dtype=float), units)
    _add_to_quantities(quantity=quantity, name=var)

    return quantities


def read_raw_data(identifier: str) -> xr.Dataset:
    """Read the raw MIPAS reference atmosphere data files as provided by RFM.

    Try to read the raw data from http://eodg.atm.ox.ac.uk/RFM/atm/
    If that fails, reads archived raw data files.
    The archived raw data files were downloaded from
    http://eodg.atm.ox.ac.uk/RFM/atm/ on June 6th, 2021.

    Parameters
    ----------
    identifier: str
        Atmospheric profile identifier in [``"day"``, ``"equ"``, ``"ngt"``,
        ``"sum"``, ``"win"``].

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    try:
        response = requests.get(f"http://eodg.atm.ox.ac.uk/RFM/atm/{identifier}.atm")
        content = response.text
    except requests.ConnectionError:
        file = f"{identifier}.atm"
        with pkg_resources.path(rfm, file) as path:
            with open(path, "r") as f:
                content = f.read()

    quantities = _parse_content(content.splitlines())
    z_level = quantities.pop("z_level")
    p = quantities.pop("p")
    t = quantities.pop("t")
    species = np.array(list(quantities.keys()))
    mr = np.array([quantities[s].magnitude for s in species])

    # compute air number density using perfect gas equation:
    n = p / (K * t)

    ds: xr.Dataset = make_data_set(
        p=p, t=t, n=n, mr=mr, z_level=z_level, species=species
    )
    return ds
