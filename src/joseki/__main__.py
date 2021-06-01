"""Command-line interface."""
import pathlib
from typing import Optional

import click


@click.command()
@click.option(
    "--identifier",
    "-i",
    help="atmospheric profile identifier",
    required=True,
    type=click.Choice(
        [
            "afgl_1986-tropical",
            "afgl_1986-midlatitude_summer",
            "afgl_1986-midlatitude_winter",
            "afgl_1986-subarctic_summer",
            "afgl_1986-subarctic_winter",
            "afgl_1986-us_standard",
        ],
        case_sensitive=True,
    ),
)
@click.option(
    "--file-name",
    "-f",
    help="output file name",
    default="ds.nc",
    type=click.Path(writable=True),
)
@click.option(
    "--level-altitudes",
    "-la",
    help="level altitudes",
    default=None,
    show_default=True,
)
@click.option(
    "--set-main-coord-to-layer-altitude",
    "-s",
    help=(
        "set the data set main coordinate to layer altitude (default is "
        "level altitude)"
    ),
    is_flag=True,
)
@click.option(
    "--p-interp-method",
    "-p",
    help="pressure interpolation method",
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
    help="temperature interpolation method",
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
    help="number density interpolation method",
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
    help="volume mixing ratios interpolation method",
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
    """Joseki."""
    print(f"identifier: {identifier}")
    print(f"level_altitudes: {level_altitudes}")
    print(f"set-main-coord-to-layer-altitude: {set_main_coord_to_layer_altitude}")
    print(f"file_name: {file_name}")
    print(f"p_interp_method: {p_interp_method}")
    print(f"t_interp_method: {t_interp_method}")
    print(f"n_interp_method: {n_interp_method}")
    print(f"x_interp_method: {x_interp_method}")
    # ds = joseki.core.make(
    #   identifier=identifier,
    #   z_level=z_level,
    #   p_interp_method=p_interp_method,
    #   t_interp_method=p_interp_method,
    #   n_interp_method=p_interp_method,
    #   x_interp_method=p_interp_method,
    #   set_main_coord_to_layer_altitude=set_main_coord_to_layer_altitude
    # )
    # ds.to_netcdf(file_name)


if __name__ == "__main__":
    main(prog_name="joseki")  # pragma: no cover
