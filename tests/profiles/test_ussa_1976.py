"""Test cases for the ussa_1976 module."""
from joseki.profiles.ussa_1976 import USSA1976

def test_ussa_1976():
    """Returns a valid dataset."""
    profile = USSA1976()
    ds = profile.to_dataset()
    assert ds.joseki.is_valid
