"""Test cases for the afgl_1986 module."""
import numpy as np
import pandas as pd
import pytest

from joseki.units import ureg
from joseki.profiles.afgl_1986 import parse
from joseki.profiles.afgl_1986 import Identifier
from joseki.profiles.afgl_1986 import to_dataset

@pytest.mark.parametrize("identifier", [n for n in Identifier])
def test_parse_returns_dataframe(identifier: Identifier) -> None:
    """Returns a pandas's DataFrame."""
    df = parse(identifier=identifier)
    assert isinstance(df, pd.DataFrame)

def test_to_dataset_z() -> None:
    """Returns a valid dataset."""
    ds = to_dataset(
        identifier=Identifier.TROPICAL,
        z=np.linspace(0, 100, 100) * ureg.km,
    )
    assert ds.joseki.is_valid
