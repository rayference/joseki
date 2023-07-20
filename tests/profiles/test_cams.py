import tempfile
from pathlib import Path

import numpy as np
import pint
import pytest
from numpy.testing import assert_almost_equal, assert_allclose

import joseki
from joseki import unit_registry as ureg
from joseki.units import to_quantity
from joseki.profiles.cams import (
    from_cams_reanalysis,
    get_molecule_amounts,
    from_archive,
    to_paths,
)


def test_from_cams_reanalysis():
    """CAMS reanalysis data can be transformed into a Joseki profile."""
    ds = from_cams_reanalysis(
        data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        identifier="EAC4",
        time="2020-07-01T00:00:00",
        lat=23.0,
        lon=28.0,
    )
    assert ds.joseki.is_valid
    expected_molecules = ["H2O", "O3"]
    assert all(m in ds.joseki.molecules for m in expected_molecules)


def test_from_cams_reanalysis_molecules_drop():
    """Unrequested molecules are dropped."""
    molecules = ["H2O"]
    ds = from_cams_reanalysis(
        data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        identifier="EAC4",
        time="2020-07-01T00:00:00",
        lat=23.0,
        lon=28.0,
        molecules=molecules,
    )
    assert ds.joseki.is_valid
    assert all(m in ds.joseki.molecules for m in molecules)


def test_from_cams_reanalysis_molecules_add():
    """Requested molecules are added."""
    molecules = ["H2O", "CO2", "O3"]
    ds = from_cams_reanalysis(
        data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        identifier="EAC4",
        time="2020-07-01T00:00:00",
        lat=23.0,
        lon=28.0,
        molecules=molecules,
        missing_molecules_from=joseki.make("afgl_1986-us_standard")
    )
    assert ds.joseki.is_valid
    assert all(m in ds.joseki.molecules for m in molecules)

def test_from_cams_reanalysis_molecules_invalid():
    """'missing_molecules_from' is not provided."""
    molecules = ["H2O", "CO2", "O3"]
    with pytest.raises(ValueError):
        from_cams_reanalysis(
            data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
            identifier="EAC4",
            time="2020-07-01T00:00:00",
            lat=23.0,
            lon=28.0,
            molecules=molecules,
        )

def test_from_cams_reanalysis_extrapolate_up():
    """Profile is extrapolated up."""
    zup = 120 * ureg.km
    ds = from_cams_reanalysis(
        data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        identifier="EAC4",
        time="2020-07-01T00:00:00",
        lat=23.0,
        lon=28.0,
        extrapolate={"up": {"z": zup}}
    )
    assert ds.joseki.is_valid
    assert_almost_equal(ds.z[-1], zup.m)

def test_from_cams_reanalysis_extrapolate_down():
    """Profile is extrapolated down."""
    zdown = - 0.01 * ureg.km
    ds = from_cams_reanalysis(
        data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        identifier="EAC4",
        time="2020-07-01T00:00:00",
        lat=23.0,
        lon=28.0,
        extrapolate={"down": {"z": zdown}}
    )
    assert ds.joseki.is_valid
    assert_almost_equal(ds.z[0], zdown.m)

def test_from_cams_reanalysis_extrapolate_invalid():
    """Raises when extrapolation specifications are invalid."""
    with pytest.raises(ValueError):
        from_cams_reanalysis(
            data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
            identifier="EAC4",
            time="2020-07-01T00:00:00",
            lat=23.0,
            lon=28.0,
            extrapolate={"invalid": "specifications"}
        )

def test_from_cams_reanalysis_regularize_bool():
    """Profile is regularized."""
    ds = from_cams_reanalysis(
        data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        identifier="EAC4",
        time="2020-07-01T00:00:00",
        lat=23.0,
        lon=28.0,
        regularize=True,
    )
    assert ds.joseki.is_valid
    zdiff = np.diff(ds.z.values)
    assert_allclose(zdiff, zdiff[0])

def test_from_cams_reanalysis_regularize_specs():
    """Profile is regularized."""
    num = 32
    ds = from_cams_reanalysis(
        data="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        identifier="EAC4",
        time="2020-07-01T00:00:00",
        lat=23.0,
        lon=28.0,
        regularize={"options": {"num": num}},
    )
    assert ds.joseki.is_valid
    assert ds.z.size == num

def test_get_molecule_amounts():
    """Returns mapping of H2O and O3 and their total amounts as quantities."""
    amounts = get_molecule_amounts(
        "tests/data/232f85b4-b3e9-47a7-a52d-9f955c38b9f6.nc",
        lat=23.0,
        lon=28.0,
        time="2020-07-01T00:00:00",
    )

    assert all([m in amounts for m in ["H2O", "O3"]])
    assert all(isinstance(k, pint.Quantity) for k in amounts.values())

def test_get_molecule_amounts_h2o():
    """Returns mapping of H2O and its total amount as quantity."""
    molecules = ["H2O"]
    amounts = get_molecule_amounts(
        "tests/data/232f85b4-b3e9-47a7-a52d-9f955c38b9f6.nc",
        lat=23.0,
        lon=28.0,
        time="2020-07-01T00:00:00",
        molecules=molecules,
    )

    assert list(amounts.keys()) == molecules

def test_get_molecule_amounts_invalid():
    """Raises because a requested molecule is not available in the CAMS data."""

    with pytest.raises(ValueError):
        get_molecule_amounts(
            "tests/data/232f85b4-b3e9-47a7-a52d-9f955c38b9f6.nc",
            lat=23.0,
            lon=28.0,
            time="2020-07-01T00:00:00",
            molecules=["CO2"],
        )

def test_from_archive():
    """Extracts in a temporary directory when 'extract_dir' is not provided."""
    path = from_archive(
        path="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
    )
    assert path.exists()

def test_from_archive_extract_dir():
    """Extracts in a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    extract_dir = Path(tmpdir)
    path = from_archive(
        path="tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb.zip",
        extract_dir=extract_dir,
    )
    assert path.exists()

def test_to_paths_invalid():

    with pytest.raises(FileNotFoundError):
        to_paths("tests/data/97dd7a58-674a-4a1f-a92b-534cb95d07bb.zip")
        ########################^ ('a' was replaced with 'd')

def test_to_paths_directory():
    paths = to_paths("tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb/")
    assert len(paths) == 2

def test_to_paths_list():
    paths = to_paths(
        [
            "tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb/levtype_ml.nc",
            "tests/data/97da7a58-674a-4a1f-a92b-534cb95d07bb/levtype_sfc.nc"
        ]
    )
    assert len(paths) == 2

def test_to_paths_invalid_type():
    with pytest.raises(NotImplementedError):
        to_paths(42)

def test_from_cams_reanalysis_pressure_data():
    """Surface pressure data is used to rescale the pressure profile."""
    ds = from_cams_reanalysis(
        data="tests/data/25b63a29-3eab-4599-92f4-7bba42ec6add.zip",
        identifier="EAC4",
        time="2021-04-01T12:00:00",
        lat=27.5,
        lon=86.5,
        pressure_data="surface_pressure",
    )

    surface_pressure = to_quantity(ds.p.isel(z=0))
    assert np.abs(surface_pressure - 1013.25 * ureg.hPa).magnitude > 1.0
