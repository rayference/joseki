"""MIPAS atmosphere thermophysical profiles.

[Remedios et al. (2007)](bibliography.md#Remedios+2007) define a set of 5 
"standard atmospheres" representing the atmosphere at different latitudes and 
seasons or times of day:

* midlatitude day
* midlatitude night
* polar winter
* polar summer
* tropical


MIPAS standard atmospheres were intended to provide an updated set of pro-
files for characteristic atmospheric states such as the
[AFGL Atmospheric constituent profiles](bibliography.md#Anderson+1986).
"""
import enum
import importlib_resources
import logging
import typing as t

import numpy as np
import pint
import xarray as xr
from attrs import define
from scipy.constants import physical_constants

from ..units import ureg
from .core import Profile, interp, DEFAULT_METHOD
from .factory import factory
from .schema import history, schema

logger = logging.getLogger(__name__)

SOURCE = "Combination of model and observational data"

REFERENCE = (
    "Remedios, John J. et al. “MIPAS reference atmospheres and comparisons to "
    "V4.61/V4.62 MIPAS level 2 geophysical data sets.” Atmospheric Chemistry "
    "and Physics 7 (2007): 9973-10017. DOI: 10.5194/ACPD-7-9973-2007"
)

INSTITUTION = "EOS, Space Research Centre, Leicester, U.K."

URL = "https://eodg.atm.ox.ac.uk/RFM/atm/"

URL_DATE = "2022-12-12"

CFC_FORMULAE = {
    "CCl3F": ("Freon-11", "F11", "R-11", "CFC-11"),
    "CCl2F2": ("Freon-12", "F12", "R-12", "CFC-12"),
    "CClF3": ("Freon-13", "F13", "R-13", "CFC-13"),
    "CF4": ("Freon-14", "F14", "CFC-14"),
    "CHClF2": ("Freon-22", "F22", "HCFC-22"),
    "CHCl2F": ("Freon-21", "F21", "HCFC-21"),
    "C2Cl3F3": ("Freon-113", "F113", "CFC-113"),
    "C2Cl2F4": ("Freon-114", "F114", "CFC-114"),
}

# Boltzmann constant
K = ureg.Quantity(*physical_constants["Boltzmann constant"][:2])


def to_chemical_formula(name: str) -> str:
    """Convert to chemical formula.
    
    Args:
        name: Molecule name.

    Returns:
        Molecule formula.
    
    Notes:
        If molecule name is unknown, returns name unchanged.
    """
    try:
        return translate_cfc(name)
    except ValueError:
        return name


def translate_cfc(name: str) -> str:
    """Convert chlorofulorocarbon name to corresponding chemical formula.

    Args:
        name: Chlorofulorocarbon name.

    Returns:
        Chlorofulorocarbon chemical formula.

    Raises:
        ValueError: If the name does not match a known chlorofulorocarbon.
    """
    for formula, names in CFC_FORMULAE.items():
        if name in names:
            return formula
    raise ValueError("Unknown chlorofulorocarbon {name}")


class Identifier(enum.Enum):
    """MIPAS atmosphere thermophysical profile identifier enumeration."""

    MIDLATITUDE_DAY = "midlatitude_day"
    MIDLATITUDE_NIGHT = "midlatitude_night"
    POLAR_WINTER = "polar_winter"
    POLAR_SUMMER = "polar_summer"
    TROPICAL = "tropical"


def parse_units(s: str) -> str:
    """Parse units."""
    if s.startswith("[") and s.endswith("]"):
        units = s[1:-1]
        if units == "mb":
            return "millibar"
        else:
            return units
    else:
        raise ValueError(f"Cannot parse units '{s}'")


def parse_var_name(n: str) -> str:
    """Parse variable name."""
    translate = {"HGT": "z", "PRE": "p", "TEM": "t"}
    if n in translate.keys():
        return translate[n]
    else:
        return to_chemical_formula(n)


def parse_var_line(s: str) -> t.Tuple[str, str]:
    """Parse a line with the declaration of a variable and its units."""
    parts = s[1:].strip().split()
    if len(parts) == 2:
        var_name, units_s = parts
    elif len(parts) == 3:
        var_name, _, units_s = parts
    else:
        raise ValueError(f"Invalid line format: {s}")
    var = parse_var_name(var_name)
    units = parse_units(units_s)
    return var, units


def parse_values_line(s: str) -> t.List[str]:
    """Parse a line with numeric values."""
    if "," in s:  # delimiter is comma and whitespace combined
        s_strip = s.strip()
        if s_strip[-1] == ",":
            s_strip = s_strip[:-1]
        return [x.strip() for x in s_strip.split(",")]
    else:  # delimiter is whitespace
        return s.split()


def parse_content(lines: t.List[str]) -> t.Dict[str, pint.Quantity]:
    """Parse lines."""
    logger.debug("Parsing file content")
    iterator = iter(lines)
    line = next(iterator)

    quantities: t.Dict[str, pint.Quantity] = {}

    def _add_to_quantities(quantity: pint.Quantity, name: str) -> None:
        if name not in ["z", "p", "t", "n"]:
            name = f"x_{name}"
        
        if quantity.check(""):
            quantities[name] = quantity.to("dimensionless")
        else:
            quantities[name] = quantity

    var: str = ""
    units: str = ""
    values: t.List[str] = []
    while line != "*END":
        if line.startswith("!"):
            pass  # this is a comment, ignore the line
        elif line.startswith("*"):
            # convert previously read values (if any) and units to quantity
            if len(values) > 0:
                quantity = ureg.Quantity(
                    np.array(values, dtype=float),
                    units,
                )
                _add_to_quantities(quantity=quantity, name=var)

            # this is a variable line, parse variable name and units
            var, units = parse_var_line(line)

            # following lines are the variables values so prepare a variable
            # to store the values
            values = []
        else:
            if "!" in line:
                # this the line with the number of profile levels, ignore it
                pass
            else:
                # this line contains variable values
                values += parse_values_line(line)
        line = next(iterator)

    # include last array of values before the '*END' line
    quantity = ureg.Quantity(np.array(values, dtype=float), units)
    _add_to_quantities(quantity=quantity, name=var)

    return quantities


def read_file_content(identifier: Identifier) -> str:
    """
    Read data file content.

    Args:
        identifier: Atmospheric profile identifier.
            See 
            [`Identifier`](reference.md#src.joseki.profiles.mipas_2007.Identifier) 
            for possible values.

    Returns:
        file content, URL, URL date.
    """
    package = "joseki.data.mipas_2007"
    file = f"{identifier.value}.atm"
    logger.debug(f"Reading file {file}")
    return importlib_resources.files(package).joinpath(file).read_text()


def get_dataset(identifier: Identifier) -> xr.Dataset:
    """Read MIPAS reference atmosphere data files into an xarray.Dataset.

    Args:
        identifier: Atmospheric profile identifier.
            See 
            [`Identifier`](reference.md#src.joseki.profiles.mipas_2007.Identifier) 
            for possible values.

    Returns:
        Atmospheric profile.
    """
    content = read_file_content(identifier=identifier)
    quantities = parse_content(content.splitlines())

    # Coordinates
    coords = {"z": quantities.pop("z")}

    # Data variables
    data_vars = {}
    p = quantities.pop("p")
    data_vars["p"] = p
    t = quantities.pop("t")
    data_vars["t"] = t
    n = p / (K * t)  # perfect gas equation
    data_vars["n"] = n
    data_vars.update(quantities)

    logger.debug("data variables: %s", data_vars.keys())

    # Attributes
    pretty_id = identifier.value.replace("_", " ")
    pretty_title = f"MIPAS {pretty_id} Reference Atmosphere"
    attrs = {
        "Conventions": "CF-1.10",
        "history": history(),
        "title": pretty_title,
        "source": SOURCE,
        "institution": INSTITUTION,
        "references": REFERENCE,
        "url": URL,
        "urldate": URL_DATE,
    }

    # Dataset
    ds = schema.convert(
        data_vars=data_vars,
        coords=coords,
        attrs=attrs,
    )

    return ds


def to_dataset(
    identifier: Identifier,
    z: t.Optional[pint.Quantity] = None,
    method: t.Optional[t.Mapping[str, str]] = None,
    conserve_column: bool = False,
    **kwargs: t.Any,
) -> xr.Dataset:
    """Helper for `Profile.to_dataset` method"""
    # no kwargs are expected
    if len(kwargs) > 0:  # pragma: no cover
        logger.warning("Unexpected keyword arguments: %s", kwargs)

    # get original MIPAS midlatitude day reference atmosphere
    logger.debug("Get original MIPAS midlatitude day reference atmosphere")
    ds = get_dataset(identifier=identifier)

    # Interpolate to new vertical grid if necessary
    if z is not None:
        method = DEFAULT_METHOD if method is None else method
        ds = interp(
            ds=ds,
            z_new=z,
            method=method,
            conserve_column=conserve_column,
        )
        return ds
    else:
        return ds


@factory.register("mipas_2007-midlatitude_day")
@define
class MIPASMidlatitudeDay(Profile):
    """MIPAS midlatitude day reference atmosphere."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        return to_dataset(
            identifier=Identifier.MIDLATITUDE_DAY,
            z=z,
            method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register("mipas_2007-midlatitude_night")
@define
class MIPASMidlatitudeNight(Profile):
    """MIPAS Midlatitude night reference atmosphere."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        return to_dataset(
            identifier=Identifier.MIDLATITUDE_NIGHT,
            z=z,
            method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register("mipas_2007-polar_summer")
@define
class MIPASPolarSummer(Profile):
    """MIPAS Polar summer reference atmosphere."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        return to_dataset(
            identifier=Identifier.POLAR_SUMMER,
            z=z,
            method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register("mipas_2007-polar_winter")
@define
class MIPASPolarWinter(Profile):
    """MIPAS Polar winter reference atmosphere."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        return to_dataset(
            identifier=Identifier.POLAR_WINTER,
            z=z,
            method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )


@factory.register("mipas_2007-tropical")
@define
class MIPASTropical(Profile):
    """MIPAS Tropical reference atmosphere."""

    def to_dataset(
        self,
        z: t.Optional[pint.Quantity] = None,
        interp_method: t.Optional[t.Mapping[str, str]] = None,
        conserve_column: bool = False,
        **kwargs: t.Any,
    ) -> xr.Dataset:
        return to_dataset(
            identifier=Identifier.TROPICAL,
            z=z,
            method=interp_method,
            conserve_column=conserve_column,
            **kwargs,
        )
