"""Module to read atmospheric profiles distributed with Reference Forward Model.

Reference Forward Model (RFM) website: http://eodg.atm.ox.ac.uk/RFM/.
"""
import enum
import importlib.resources as pkg_resources
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np
import requests
import xarray as xr
from scipy.constants import physical_constants

from .data import rfm
from .units import ureg
from .util import make_data_set
from .util import to_chemical_formula

SOURCE = "unknown"

REFERENCE = "unknown"

DESCRIPTION = {
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


class Identifier(enum.Enum):
    """RFM atmospheric profile identifier enumeration."""

    WIN = "win"
    SUM = "sum"
    DAY = "day"
    NGT = "ngt"
    EQU = "equ"
    DAY_IMK = "day_imk"
    NGT_IMK = "ngt_imk"
    SUM_IMK = "sum_imk"
    WIN_IMK = "win_imk"
    MLS = "mls"
    MLW = "mlw"
    SAS = "sas"
    SAW = "saw"
    STD = "std"
    TRO = "tro"


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
    translate = {"HGT": "z", "PRE": "p", "TEM": "t"}
    if n in translate.keys():
        return translate[n]
    else:
        return to_chemical_formula(n)


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


def read_file_content(identifier: Identifier) -> Tuple[str, Dict[str, str]]:
    """
    Read atmospheric profile data file content.

    Parameters
    ----------
    identifier: Identifier
        Atmospheric profile identifier.
        See :class:`.Identifier` for possible values.

    Returns
    -------
    tuple:
        file content, URL, URL date.
    """
    file_name = identifier.value.split("-")[-1]
    return _read_file_content(file_name=file_name)


def _read_file_content(file_name: str) -> Tuple[str, Dict[str, str]]:
    """
    Read data file content.

    Parameters
    ----------
    file_name: str
        Atmospheric data file name.

    Returns
    -------
    tuple:
        file content, URL, URL date.
    """
    try:
        url = f"http://eodg.atm.ox.ac.uk/RFM/atm/{file_name}.atm"
        url_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = requests.get(url)
        content = response.text
        return content, dict(url=url, url_date=url_date)
    except requests.ConnectionError:
        file = f"{file_name}.atm"
        with pkg_resources.path(rfm, file) as path:
            with open(path, "r") as f:
                content = f.read()
        return content, dict()


def read_additional_molecules(
    identifier: Identifier,
) -> Tuple[Dict[str, ureg.Quantity], Dict[str, str]]:
    """
    Read additional molecules data file.

    Parameters
    ----------
    identifier: Identifier
        Atmospheric profile identifier.
        See :class:`.Identifier` for possible values.

    Returns
    -------
    tuple of dict of str and :class:`~pint.Quantity` and dict of str and str:
        Additional molecules parsed content, URL information.
    """
    if identifier in [
        Identifier.DAY,
        Identifier.EQU,
        Identifier.NGT,
        Identifier.SUM,
        Identifier.WIN,
    ]:
        add_molecules_name = "extra"
    if identifier in [
        Identifier.DAY_IMK,
        Identifier.NGT_IMK,
        Identifier.SUM_IMK,
        Identifier.WIN_IMK,
    ]:
        add_molecules_name = "extra_imk"
    if identifier in [
        Identifier.MLS,
        Identifier.MLW,
        Identifier.SAS,
        Identifier.SAW,
        Identifier.STD,
        Identifier.TRO,
    ]:
        add_molecules_name = "minor"

    content, url_info = _read_file_content(file_name=add_molecules_name)
    parsed_content = _parse_content(content.splitlines())
    return parsed_content, url_info


def read(
    identifier: Identifier, additional_molecules: Optional[bool] = False
) -> xr.Dataset:
    """Read RFM atmospheric data files.

    Try to read the data from http://eodg.atm.ox.ac.uk/RFM/atm/
    If that fails, reads archived data files in ``src/joseki/data/rfm/``.
    The archived raw data files were downloaded from
    http://eodg.atm.ox.ac.uk/RFM/atm/ on June 6th, 2021.

    Parameters
    ----------
    identifier: Identifier
        Atmospheric profile identifier.
        See :class:`.Identifier` for possible values.

    additional_molecules: bool
        Set to ``True`` to include the additional molecules to the atmospheric
        profile.

    Returns
    -------
    :class:`~xarray.Dataset`
        Atmospheric profile.
    """
    content, url_info = read_file_content(identifier=identifier)
    url = url_info.get("url")
    url_date = url_info.get("url_date")
    quantities = _parse_content(content.splitlines())

    z = quantities.pop("z")
    p = quantities.pop("p")
    t = quantities.pop("t")
    n = p / (K * t)  # perfect gas equation
    molecules = np.array(list(quantities.keys()))
    x = np.array([quantities[molecule].magnitude for molecule in molecules])

    if additional_molecules:
        extra_quantities, extra_url_info = read_additional_molecules(
            identifier=identifier
        )
        extra_z = extra_quantities.pop("z")
        extra_molecules = np.array(list(extra_quantities.keys()))
        extra_x = np.array([extra_quantities[s].magnitude for s in extra_molecules])

        # initial molecules
        da = xr.DataArray(
            x,
            dims=["molecules", "z"],
            coords={"molecules": molecules, "z": z.magnitude},
        )

        # additional molecules
        da_extra = xr.DataArray(
            extra_x,
            dims=["molecules", "z"],
            coords={
                "molecules": extra_molecules,
                "z": extra_z.m_as(z.units),
            },
        )

        # interpolate additional molecules mixing ratio on altitude mesh used
        # for initial molecules mixing ratio:
        da_extra_interp = np.exp(np.log(da_extra).interp(z=z.m_as(z.units)))

        # concatenate initial and additional molecules
        da_total = xr.concat([da, da_extra_interp], dim="molecules")
        molecules = da_total.molecules.values
        x = da_total.values

    ds: xr.Dataset = make_data_set(
        p=p,
        t=t,
        n=n,
        x=x,
        z=z,
        molecules=molecules,
        func_name="joseki.rfm.read",
        operation="data set creation",
        title=f"RFM {DESCRIPTION[identifier.value]} atmospheric profile",
        source=SOURCE,
        references=REFERENCE,
        url=url,
        url_date=url_date,
    )
    return ds
