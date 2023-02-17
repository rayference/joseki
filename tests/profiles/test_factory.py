import pytest

from joseki.profiles.factory import factory


def test_create():
    with pytest.raises(ValueError):
        factory.create(identifier="invalid")