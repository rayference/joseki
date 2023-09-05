# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2023-09-05

### Added

* Units definition file at `data/units.txt`
* Quantity conversion for `z` parameter of `make`, which makes it possible to
  use `make` with pure Python inputs

### Changed

* Get unit registry from application and add Joseki required units by loading 
  a units definition file.

### Removed

* CAMS reanalysis datasets support
 
## [2.4.0] - 2023-08-07

### Added

* parameter `regularize` to `make`.
* parameters `rescale_to` and `check_x_sum` to `make`.
* Tests for `make` with parameters `regularize` and `rescale_to`
* Instructions to run tests and verify test coverage for maintainers

### Changed

* Project was moved to the [Rayference](https://github.com/rayference) organization.
* Interpolate in time in the last step in `from_cams_reanalysis`

### Removed

* `represent_in_cells` and related.

## [2.3.0] - 2023-07-20

### Added

* maintainers guide at `maintainers.md`
* Added `merge` method to merge multiple profiles together
* Maintainers guide: added a section on how to modify the tutorials 

### Changed

* update `CITATION.cff` for version `2.2.0`
* change `pressure_data` default value to `"surface_pressure"` in 
  `from_cams_reanalysis` 
* in `from_cams_reanalysis()`, interpolate along time, longitude and latitude 
  instead of selecting the nearest neighbour.

### Fixed

* Link to documentation in `README.md`
* Wrong latitude and longitude coordinates in tutorials 
* Added `merge` method to merge multiple profiles together

## [2.2.0] - 2023-07-18

### Added

* Add `mike` to the `docs` dependencies group
* Documentation versioning
* `molecules` parameter to `joseki.make` to select the molecules to be 
  included in the profile.
* `select_molecules` method in `joseki.profiles.core` to select the
  molecules to be included in the profile.
* `drop_molecules` accessor method to drop mole fraction data for specified 
  molecules.
* Test that surface pressure is used to rescale pressure profile.
* Parameter pressure_data to `joseki.profiles.from_cams_reanalysis` to 
  indicate how to compute the pressure profile (either with or without
  rescaling with the surface pressure).
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

* Rename *volume (mixing) fraction* -> *mole fraction*.
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



    