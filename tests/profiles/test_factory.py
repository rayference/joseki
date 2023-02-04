import pytest

from joseki.profiles.factory import factory


def test_create() -> None:
    with pytest.raises(ValueError):
        factory.create(identifier="invalid")