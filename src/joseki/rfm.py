"""Module to read atmospheric profiles distributed with Reference Forward Model.

Reference Forward Model (RFM) website: http://eodg.atm.ox.ac.uk/RFM/.
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
from joseki import util

SOURCE = "Unknown"

REFERENCE = "Unknown"

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
        return util.to_chemical_formula(n)


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


def read(name: str) -> xr.Dataset:
    """Read RFM atmospheric data files.

    Try to read the data from http://eodg.atm.ox.ac.uk/RFM/atm/
    If that fails, reads archived data files in ``src/joseki/data/rfm/``.
    The archived raw data files were downloaded from
    http://eodg.atm.ox.ac.uk/RFM/atm/ on June 6th, 2021.

    Parameters
    ----------
    name: str
        Atmospheric profile name in [``"day"``, ``"day_imk"``, ``"equ"``,
        ``"ngt"``, ``"ngt_imk"``, ``"sum"``, ``"sum_imk"``, ``"win"``,
        ``"win-imk"``, ``"mls"``, ``"mlw"``, ``"sas"``, ``"saw"``, ``"std"``,
        ``"tro"``].

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    try:
        response = requests.get(f"http://eodg.atm.ox.ac.uk/RFM/atm/{name}.atm")
        content = response.text
    except requests.ConnectionError:
        file = f"{name}.atm"
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

    translate = {
        "win": "MIPAS (2001) polar winter",
        "sum": "MIPAS (2001) polar summer",
        "day": "MIPAS (2001) mid-latitude daytime",
        "ngt": "MIPAS (2001) mid-latitude nighttime",
        "equ": "MIPAS (2001) equatorial",
        "day_imk": "MIPAS (1998) mid-latitude daytime",
        "ngt_imk": "MIPAS (1998) mid-latitude nighttime",
        "sum_imk": "MIPAS (1998) polar summer",
        "win_imk": "MIPAS (1998) polar winter",
        "mls": "AFGL (1986) Mid-latitude summer",
        "mlw": "AFGL (1986) Mid-latitude winter",
        "sas": "AFGL (1986) Sub-arctic summer",
        "saw": "AFGL (1986) Sub-arctic winter",
        "std": "AFGL (1986) U.S. Standard",
        "tro": "AFGL (1986) Tropical",
    }

    ds: xr.Dataset = util.make_data_set(
        p=p,
        t=t,
        n=n,
        mr=mr,
        z_level=z_level,
        species=species,
        title=f"RFM {translate[name]} atmospheric profile",
        source=SOURCE,
        references=REFERENCE,
        func_name="joseki.rfm.read",
        operation="data set creation",
    )
    return ds
