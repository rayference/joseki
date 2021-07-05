"""Command-line interface."""
import pathlib
from typing import Optional

import click

from .core import make


@click.command()
@click.option(
    "--file-name",
    "-f",
    help="Output file name.",
    default="ds.nc",
    type=click.Path(writable=True),
)
@click.option(
    "--identifier",
    "-i",
    help="Atmospheric profile identifier.",
    required=True,
    type=click.Choice(
        [
            "afgl_1986-tropical",
            "afgl_1986-midlatitude_summer",
            "afgl_1986-midlatitude_winter",
            "afgl_1986-subarctic_summer",
            "afgl_1986-subarctic_winter",
            "afgl_1986-us_standard",
            "rfm-day",
            "rfm-equ",
            "rfm-ngt",
            "rfm-sum",
            "rfm-win",
        ],
        case_sensitive=True,
    ),
)
@click.option(
    "--altitudes",
    "-a",
    help=(
        "Path to level altitudes data file. The data file is read with "
        ":meth:`numpy.loadtxt`."
    ),
    default=None,
    show_default=True,
)
@click.option(
    "--represent-in-cells",
    "-r",
    help=(
        "Compute the cells representation of the atmospheric profile. The "
        "initial altitude values are used to define the altitude bounds of "
        "each cell. The pressure, temperature, number density and mixing "
        "ratio fields are interpolated at the cells' center altitudes."
    ),
    is_flag=True,
)
@click.option(
    "--p-interp-method",
    "-p",
    help="Pressure interpolation method.",
    type=click.Choice(
        [
            "linear",
            "nearest",
            "nearest-up",
            "zero",
            "slinear",
            "quadratic",
            "cubic",
            "previous",
            "next",
        ],
        case_sensitive=True,
    ),
    default="linear",
)
@click.option(
    "--t-interp-method",
    "-t",
    help="Temperature interpolation method.",
    type=click.Choice(
        [
            "linear",
            "nearest",
            "nearest-up",
            "zero",
            "slinear",
            "quadratic",
            "cubic",
            "previous",
            "next",
        ],
        case_sensitive=True,
    ),
    default="linear",
)
@click.option(
    "--n-interp-method",
    "-n",
    help="Number density interpolation method.",
    type=click.Choice(
        [
            "linear",
            "nearest",
            "nearest-up",
            "zero",
            "slinear",
            "quadratic",
            "cubic",
            "previous",
            "next",
        ],
        case_sensitive=True,
    ),
    default="linear",
)
@click.option(
    "--x-interp-method",
    "-x",
    help="Volume mixing ratios interpolation method.",
    type=click.Choice(
        [
            "linear",
            "nearest",
            "nearest-up",
            "zero",
            "slinear",
            "quadratic",
            "cubic",
            "previous",
            "next",
        ],
        case_sensitive=True,
    ),
    default="linear",
)
@click.version_option()
def main(
    file_name: str,
    identifier: str,
    altitudes: Optional[pathlib.Path],
    represent_in_cells: bool,
    p_interp_method: str,
    t_interp_method: str,
    n_interp_method: str,
    x_interp_method: str,
) -> None:
    """Joseki command-line interface."""
    ds = make(
        identifier=identifier,
        altitudes=altitudes,
        p_interp_method=p_interp_method,
        t_interp_method=t_interp_method,
        n_interp_method=n_interp_method,
        x_interp_method=x_interp_method,
        represent_in_cells=represent_in_cells,
    )
    ds.to_netcdf(file_name)


if __name__ == "__main__":
    main(prog_name="joseki")  # pragma: no cover
