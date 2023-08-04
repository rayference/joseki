"""Command-line interface."""
import pathlib
import typing as t

import click
import pandas as pd

from .core import make
from .units import ureg
from .profiles.factory import factory

IDENTIFIER_CHOICES = factory.registered_identifiers

INTERPOLATION_METHOD_CHOICES = [
    "linear",
    "nearest",
    "nearest-up",
    "zero",
    "slinear",
    "quadratic",
    "cubic",
    "previous",
    "next",
]


@click.command()
@click.option(
    "--file-name",
    "-f",
    help="Output file name.",
    default="ds.nc",
    show_default=True,
    type=click.Path(writable=True),
)
@click.option(
    "--identifier",
    "-i",
    help="Atmospheric profile identifier.",
    required=True,
    type=click.Choice(
        choices=IDENTIFIER_CHOICES,
        case_sensitive=True,
    ),
)
@click.option(
    "--altitudes",
    "-a",
    help=(
        "Path to level altitudes data file. The data file is read with "
        "pandas.read_csv. The data file must be a column named 'z'."
    ),
    default=None,
    show_default=True,
)
@click.option(
    "--altitude-units",
    "-u",
    help="Altitude units",
    default="km",
    show_default=True,
)
@click.option(
    "--conserve-column",
    "-c",
    help=(
        "Ensure that column densities are conserved during interpolation."
    ),
    is_flag=True,
)
@click.option(
    "--p-interp-method",
    "-p",
    help="Pressure interpolation method.",
    type=click.Choice(
        INTERPOLATION_METHOD_CHOICES,
        case_sensitive=True,
    ),
    default="linear",
    show_default=True,
)
@click.option(
    "--t-interp-method",
    "-t",
    help="Temperature interpolation method.",
    type=click.Choice(
        INTERPOLATION_METHOD_CHOICES,
        case_sensitive=True,
    ),
    default="linear",
    show_default=True,
)
@click.option(
    "--n-interp-method",
    "-n",
    help="Number density interpolation method.",
    type=click.Choice(
        INTERPOLATION_METHOD_CHOICES,
        case_sensitive=True,
    ),
    default="linear",
    show_default=True,
)
@click.option(
    "--x-interp-method",
    "-x",
    help="Volume mixing ratios interpolation method.",
    type=click.Choice(
        INTERPOLATION_METHOD_CHOICES,
        case_sensitive=True,
    ),
    default="linear",
    show_default=True,
)
@click.version_option()
def main(
    file_name: str,
    identifier: str,
    altitudes: t.Optional[str],
    altitude_units: str,
    conserve_column: bool,
    p_interp_method: str,
    t_interp_method: str,
    n_interp_method: str,
    x_interp_method: str,
) -> None:
    """Joseki command-line interface."""
    # read altitude grid
    if altitudes is not None:
        df = pd.read_csv(pathlib.Path(altitudes))
        z = df["z"].values * ureg(altitude_units)
    else:
        z = None

    interp_method = {
        "p": p_interp_method,
        "t": t_interp_method,
        "n": n_interp_method,
        "x": x_interp_method,
        "default": "linear",
    }

    # make dataset
    ds = make(
        identifier=identifier,
        z=z,
        interp_method=interp_method,
        conserve_column=conserve_column,
    )

    # write dataset
    ds.to_netcdf(file_name)


if __name__ == "__main__":
    main(prog_name="joseki")  # pragma: no cover
