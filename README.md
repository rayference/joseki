# Joseki

Reference atmosphere's thermophysical profiles for radiative transfer
applications in Earth's atmosphere.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![code-style-black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI](https://img.shields.io/pypi/v/joseki)](https://pypi.python.org/pypi/joseki/)
[![Coverage](https://codecov.io/gh/nollety/joseki/branch/main/graph/badge.svg)](https://codecov.io/gh/nollety/joseki)


This package gathers together datasets of thermophysical properties of the
Earth's atmosphere relevant for radiative transfer applications, and provides
utilities to compute common caracteristic quantities as well as to perform
different operations, such as interpolation and rescaling, on a dataset.

## Features

* Available profiles:
  * *AFGL Atmospheric Constituent Profiles (0-120 km)*
  * *MIPAS (2007) reference atmospheres*
  * *U.S. Standard Atmosphere, 1976*
* Specify the altitude mesh to interpolate the atmospheric profile at.
* Move from the nodes-representation to the cells-representation of the 
  altitude mesh.
* Command-line interface.
* Python API.


## Requirements

* Python 3.8+


## Installation

You can install *Joseki* via `pip` from [`PyPI`](https://pypi.org/):

```shell
pip install joseki
```

## Documentation

Visit https://nollety.github.io/joseki/.