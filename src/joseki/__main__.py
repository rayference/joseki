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
            "mipas_rfm-day",
            "mipas_rfm-equ",
            "mipas_rfm-ngt",
            "mipas_rfm-sum",
            "mipas_rfm-win",
        ],
        case_sensitive=True,
    ),
)
@click.option(
    "--level-altitudes",
    "-la",
    help=(
        "Path to level altitudes data file. The data file is read with "
        ":meth:`numpy.loadtxt`."
    ),
    default=None,
    show_default=True,
)
@click.option(
    "--set-main-coord-to-layer-altitude",
    "-s",
    help=(
        "Set the data set main coordinate to layer altitude (default is "
        "level altitude)."
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
    level_altitudes: Optional[pathlib.Path],
    set_main_coord_to_layer_altitude: bool,
    p_interp_method: str,
    t_interp_method: str,
    n_interp_method: str,
    x_interp_method: str,
) -> None:
    """Joseki command-line interface."""
    ds = make(
        identifier=identifier,
        level_altitudes=level_altitudes,
        p_interp_method=p_interp_method,
        t_interp_method=t_interp_method,
        n_interp_method=n_interp_method,
        x_interp_method=x_interp_method,
        main_coord_to_layer_altitude=set_main_coord_to_layer_altitude,
    )
    ds.to_netcdf(file_name)


if __name__ == "__main__":
    main(prog_name="joseki")  # pragma: no cover
