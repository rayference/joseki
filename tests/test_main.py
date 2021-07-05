"""Test cases for the __main__ module."""
from typing import Any

import pytest
from click.testing import CliRunner

from joseki import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_main_succeeds(runner: CliRunner, tmpdir: Any) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(
        __main__.main,
        ["--identifier=afgl_1986-tropical", f"--file-name={tmpdir / 'ds.nc'}"],
    )
    assert result.exit_code == 0


def test_main_set_main_coord_to_layer_altitude(runner: CliRunner, tmpdir: Any) -> None:
    """Exits with a status code of zero with option '-s'."""
    result = runner.invoke(
        __main__.main,
        [
            "--identifier=afgl_1986-tropical",
            f"--file-name={tmpdir / 'ds.nc'}",
            "--set-main-coord-to-layer-altitude",
        ],
    )
    assert result.exit_code == 0
