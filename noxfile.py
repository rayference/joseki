"""Nox sessions."""
import os

import nox


def _has_venv(session):
    return not isinstance(session.virtualenv, nox.virtualenv.PassthroughEnv)


@nox.session(python=("3.8", "3.9", "3.10"))
def test(session):
    """Run the test suite."""

    # If a virtual environment is used, configure PDM appropriately and install
    # If --no-venv is used, the install step is skipped
    if _has_venv(session):
        os.environ.update({"PDM_USE_VENV": "1", "PDM_IGNORE_SAVED_PYTHON": "1"})
        session.run("pdm", "install", "-G", "test", external=True)

    # Allow passing arguments to pytest
    # Example: nox --no-venv -s test -- tests/my_test.py
    args = session.posargs if session.posargs else []
    session.run(
        "pdm",
        "run",
        "coverage",
        "run",
        "-m",
        "pytest",
        *args,
        external=True,
    )