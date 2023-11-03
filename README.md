<p align="center">
<img align="center" alt="Joseki logo" src="logo.svg"  width=100 style="margin-right: 10px; border-radius: 20%"/>
</p>

# Joseki

Reference atmosphere's thermophysical profiles for radiative transfer
applications in Earth's atmosphere.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![code-style-black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI](https://img.shields.io/pypi/v/joseki)](https://pypi.python.org/pypi/joseki/)
[![Conda](https://img.shields.io/conda/vn/conda-forge/joseki)](https://anaconda.org/conda-forge/joseki)
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
* NetCDF support thanks to the [xarray](https://xarray.pydata.org) library
* Documented and standard dataset format based on the 
  [CF conventions](https://cfconventions.org)
* Dataset schema validation
* Altitude interpolation/extrapolation and regularization
* Molecular concentration rescaling
* Molecules selection
* Computation of derived quantities
* Convenient units support thanks to the [pint](https://pint.readthedocs.io) 
  library
* Command-line interface
* Python API


## Requirements

* Python 3.8+


## Installation

You can install *Joseki* via [`pip`](https://pip.pypa.io/en/stable/) from 
[`PyPI`](https://pypi.org/):

```shell
pip install joseki
```

or via [`conda`](https://docs.conda.io) from 
[`conda-forge`](https://conda-forge.org):

```shell
conda install -c conda-forge joseki
```

## Documentation

Visit https://rayference.github.io/joseki/latest.

## Ikigai

*Joseki* was born in the context of the development of the 
[Eradiate](https://github.com/eradiate/eradiate) radiative transfer model, from
the need to collect, document and trace, integrate and modify *popular* 
thermophysical profiles.
As such, its features evolve in close relationship to those of *Eradiate*.

## About

Joseki is written and maintained by [Yvan Nollet](https://github.com/nollety).

Development is supported by [Rayference](https://www.rayference.eu).

Joseki is a component of the [Eradiate radiative transfer model](https://www.eradiate.eu/site/).

Joseki's logo is a simple representation (not to scale!) of the 5 layers of Earth's atmosphere (troposphere, stratosphere, mesosphere, thermosphere and exosphere).
