"""Test cases for the afgl_1986 module."""
import numpy as np
import pandas as pd
import pytest

from joseki.units import ureg
from joseki.profiles.afgl_1986 import parse
from joseki.profiles.afgl_1986 import Identifier
from joseki.profiles.afgl_1986 import to_dataset


@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_parse_returns_dataframe(identifier: Identifier):
    """Returns a pandas's DataFrame."""
    df = parse(identifier=identifier)
    assert isinstance(df, pd.DataFrame)


def test_to_dataset_z():
    """Returns a valid dataset."""
    ds = to_dataset(
        identifier=Identifier.TROPICAL,
        z=np.linspace(0, 100, 100) * ureg.km,
    )
    assert ds.joseki.is_valid


def test_to_dataset_additional_molecules():
    """
    Number of molecules in returned dataset is 28 when 'additional_molecules'
    is set to True, and 7 when set to False.
    Additional keyword arguments are ignored.
    """

    # Without additional_molecules, there are 7 molecules.
    ds = to_dataset(
        identifier=Identifier.TROPICAL,
        additional_molecules=False,
    )

    assert len(ds.joseki.molecules) == 7

    # With additional_molecules, there are 28 molecules.
    ds = to_dataset(
        identifier=Identifier.TROPICAL,
        additional_molecules=True,
    )

    assert len(ds.joseki.molecules) == 28

    # Other kwargs are ignored.
    ds = to_dataset(
        identifier=Identifier.TROPICAL,
        additional_molecules=True,
        ignore="this",
    )

    assert len(ds.joseki.molecules) == 28
