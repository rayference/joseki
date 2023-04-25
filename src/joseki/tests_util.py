"""Test utilities."""

from pathlib import Path  # pragma: no cover

def find_test_data(filename: str) -> Path:  # pragma: no cover
    """Find a test data file."""
    this_file = Path(__file__)  # JOSEKI_ROOT/src/joseki/tests_util.py
    joseki_root = this_file.parent.parent.parent  # JOSEKI_ROOT

    # JOSEKI_ROOT/tests/data/filename    
    return joseki_root / "tests/data" / filename 
