"""Test cases for the __main__ module."""
import pathlib
import typing as t

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from click.testing import CliRunner

from joseki import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.mark.parametrize(
    "identifier", ["afgl_1986-midlatitude_summer", "mipas_2007-midlatitude_day"]
)
def test_main_succeeds(runner: CliRunner, tmpdir: t.Any, identifier: str) -> None:
    """Exits with a status code of zero."""
    result = runner.invoke(
        __main__.main,
        [f"--identifier={identifier}", f"--file-name={tmpdir / 'ds.nc'}"],
    )
    assert result.exit_code == 0


def test_main_open_data_set(runner: CliRunner, tmpdir: t.Any) -> None:
    """Returns a xarray.Dataset."""
    path = pathlib.Path(tmpdir / "ds.nc")
    runner.invoke(
        __main__.main,
        ["--identifier=afgl_1986-tropical", f"--file-name={path}"],
    )
    assert isinstance(xr.open_dataset(path), xr.Dataset)


@pytest.fixture
def altitudes_path(tmpdir: t.Any) -> pathlib.Path:
    """Fixture for altitudes file path."""
    df = pd.DataFrame(np.linspace(0, 120, 121), columns=["z"])
    path = pathlib.Path(tmpdir, "z.csv")
    df.to_csv(path)
    return path


def test_main_altitude_path(
    runner: CliRunner, tmpdir: t.Any, altitudes_path: pathlib.Path
) -> None:
    """Exits with a status code of zero when --altitudes option is used."""
    result = runner.invoke(
        __main__.main,
        [
            "--identifier=afgl_1986-tropical",
            f"--file-name={tmpdir / 'ds.nc'}",
            f"--altitudes={altitudes_path}",
        ],
    )
    assert result.exit_code == 0


def test_main_represent_in_cells(runner: CliRunner, tmpdir: t.Any) -> None:
    """Exits with a status code of zero with option --represent-in-cells."""
    result = runner.invoke(
        __main__.main,
        [
            "--identifier=afgl_1986-tropical",
            f"--file-name={tmpdir / 'ds.nc'}",
            "--represent-in-cells",
        ],
    )
    assert result.exit_code == 0
