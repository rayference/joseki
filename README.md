# Joseki

Reference atmosphere's thermophysical profiles for radiative transfer
applications in Earth's atmosphere.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![code-style-black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This package gathers together data sets of thermophysical properties of the
Earth's atmosphere relevant for radiative transfer applications, and provides
utilities to compute common caracteristic quantities as well as to perform
different operations, such as interpolation and rescaling, on a data set.

## Features

* Available profiles:
  * *AFGL Atmospheric Constituent Profiles (0-120 km)*
  * *MIPAS (2007) reference atmospheres*
  * *U.S. Standard Atmosphere, 1976*
* Profiles interpolation along the altitude.
* Projection of the nodes-based profile on the corresponding centers-based altitude mesh.
* Command-line interface.
* Python API.


## Requirements

* Python 3.8+


## Installation

You can install *Joseki* via `pip` from [`PyPI`](https://pypi.org/):

```shell
pip install joseki
```
