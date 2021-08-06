"""Test cases for the __main__ module."""
import pathlib
from typing import Any

import numpy as np
import pytest
import xarray as xr
from click.testing import CliRunner

from joseki import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.mark.parametrize("identifier", __main__.IDENTIFIER_CHOICES)
def test_main_succeeds(runner: CliRunner, tmpdir: Any, identifier: str) -> None:
    """Exits with a status code of zero."""
    result = runner.invoke(
        __main__.main,
        [f"--identifier={identifier}", f"--file-name={tmpdir / 'ds.nc'}"],
    )
    assert result.exit_code == 0


def test_main_open_data_set(runner: CliRunner, tmpdir: Any) -> None:
    """Returns a xarray.Dataset."""
    path = pathlib.Path(tmpdir / "ds.nc")
    runner.invoke(
        __main__.main,
        ["--identifier=afgl_1986-tropical", f"--file-name={path}"],
    )
    assert isinstance(xr.open_dataset(path), xr.Dataset)  # type: ignore


@pytest.fixture
def altitudes_path(tmpdir: Any) -> pathlib.Path:
    """Fixture for altitudes file path."""
    z_values = np.linspace(0, 120, 121)
    path = pathlib.Path(tmpdir, "z.txt")
    np.savetxt(path, z_values)  # type: ignore[no-untyped-call]
    return path


def test_main_altitude_path(
    runner: CliRunner, tmpdir: Any, altitudes_path: pathlib.Path
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


def test_main_represent_in_cells(runner: CliRunner, tmpdir: Any) -> None:
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
