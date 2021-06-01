"""Sphinx configuration."""
from datetime import datetime


project = "Joseki"
author = "Yvan Nollet"
copyright = f"{datetime.now().year}, {author}"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "sphinxcontrib.bibtex",
]
autodoc_typehints = "description"
bibtex_bibfiles = ["references.bib"]
html_theme = "furo"
intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "pint": ("https://pint.readthedocs.io/en/stable/", None),
    "xarray": ("http://xarray.pydata.org/en/stable/", None),
}
