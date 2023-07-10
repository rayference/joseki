# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Test CAMS data in `joseki/tests/data`.
* Tests for `joseki.profiles.cams` module.
* Tests for `joseki.core.regularize` and `joseki.core.extrapolate`.
* `joseki.core.regularize` function.
* `joseki.core.extrapolate` function.
* `rescale_to` accessor method.
* `interp` function to API.
* Tutorials about CAMS reanalysis datasets.
* ECMWF data under `joseki.data.ecmwf`.
* `joseki.profiles.cams` module to process the reanalysis datasets from the  
  Copernicus Atmosphere Monitoring Service (CAMS).
* `joseki.constants` module to host constants.
* `joseki.profiles.util` utility module.
* `mass_fraction` and `air_molar_mass` properties to accessor.
* Functions to compute volume fraction from mass fraction.
* `rescale_to` accessor method.

### Fixed

* Fix `rescale_to_column` accessor method.

### Changed

* Updated `joseki.units` tests.
* `joseki.units.to_quantity` is dispatched against `pint.Quantity`, `dict`, 
  `int`, `float`, `list`, `numpy.ndarray` and `xarray.DataArray`.
* `joseki.core.interp`: sort input altitudes before interpolating, and pop
  `"bounds_error"` and `"kind"` from `kwargs`.
* Moved constants from `joseki.accessor` to `joseki.constants`.
* What was referred to as *volume fraction* is now referred to as 
  *mole fraction*.
* Rename `check_volume_fraction_sum` -> `check_x_sum`.
* Make number density optional in `Schema.convert`.
* Make `interp` accept keyword arguments.
* Change the changelog format to comply with 
  [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.1.0] - 2023-02-17

### Added

* Installation instructions for *conda*
* All missing HITRAN species
* Thin wrappers for `xarray.open_dataset` and `xarray.load_dataset`
* Convenience method to list available identifiers

### Fixed

* Fix out-dated command-line interface

### Changed

* Lower version constraint on *Numpy*


## [2.0.0] - 2023-02-14

### Added

* Profile factory
* Profile dataset schema converter and validator
* Logging

### Changed

* Move from Poetry to [PDM](https://pdm.fming.dev/)
* Re-organize documentation content
* Move from Sphinx to [mkdocs](https://www.mkdocs.org/)



    