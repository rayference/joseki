"""Module to read MIPAS atmospheric profiles.

Data are provided by RFM (http://eodg.atm.ox.ac.uk/RFM/).
"""
from typing import Dict
from typing import List

import numpy as np
import requests
import xarray as xr

from joseki import ureg
from joseki.core import make_data_set


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


def _parse_content(lines: List[str]) -> Dict[str, ureg.Quantity]:
    """Parse lines."""
    iterator = iter(lines)
    line = next(iterator)

    quantities: Dict[str, ureg.Quantity] = {}
    var: str = ""
    units: str = ""
    values: List[str] = []
    while line != "*END":
        if line.startswith("!"):
            # this is a comment, ignore the line
            pass
        elif line.startswith("*"):
            if len(values) > 0:
                quantity = ureg.Quantity(np.array(values, dtype=float), units)
                if units == "ppmv":
                    quantities[var] = quantity.to("dimensionless")
                else:
                    quantities[var] = quantity

            # this is a variable line, fetch variable name and units
            var_name, units_s = line[1:].strip().split(" ")
            var = _parse_var_name(var_name)
            units = _parse_units(units_s)

            # following lines are the variables values so prepare a variable
            # to store the values
            values = []
        else:
            if "!" in line:
                # this the line with the number of profile levels, ignore it
                pass
            else:
                # this line contains variable values
                values += line.split()
        line = next(iterator)

    return quantities


def read_raw_mipas_data(identifier: str) -> xr.Dataset:
    """Read the raw MIPAS reference atmosphere data files.

    The data files were downloaded from http://eodg.atm.ox.ac.uk/RFM/atm/ on
    June 6th, 2021.

    Parameters
    ----------
    identifier: str
        Atmospheric profile identifier in [``"day"``].

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    response = requests.get("http://eodg.atm.ox.ac.uk/RFM/atm/{identifier}.atm")
    quantities = _parse_content(response.text.splitlines())
    z_level = quantities.pop("z_level")
    p = quantities.pop("p")
    t = quantities.pop("t")
    species = list(quantities.keys())
    mr = np.array([quantities[s].magnitude for s in species])
    ds: xr.Dataset = make_data_set(
        p=p, t=t, n=None, mr=mr, z_level=z_level, species=species
    )
    return ds
