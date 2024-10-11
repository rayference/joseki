# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.2]

### Fixed

* Reduced logging level of updates during factory registration.

## [2.6.1] - 2024-02-13

### Changed

* Various documentation tweaks for improved quality of life (search, logo, etc.).
* Move from PDM to [Rye](https://rye-up.com/) for project management.

### Fixed

* Added missing tests to bring coverage metric to 100%.

## [2.6.0] - 2023-12-14

### Changed

* Joseki is now licensed under the terms of the LGPLv3.
* Updated documentation to reflect licensing and governance changes.
* Added Python 3.11 and 3.12 to CI matrix: Joseki is now testing with Python 3.8
  to 3.12.

## [2.5.2] - 2023-11-16

### Added

* Unit test for `joseki.profiles.schema`
* Unit test for `joseki.profiles.util`
* Unit test for `joseki.units`

### Fixed

* Remove duplicate definition of 'parts_per_billion' unit
  ([#356](https://github.com/rayference/joseki/pull/356))

## [2.5.1] - 2023-10-03

### Added

* Logo

### Changed

* Schema: accept other units for data variables and data coordinates as long as
  they match the expected dimensionality
* Units registry: load unit definitions one by one in a try-except logic

### Fixed

* Accessor `is_valid` did not return `False` when a dataset does not comply
  with the schema.

### Removed

* Obsolete test data
* Obsolete documentation figures
* Obsolete module `test_util.py`

## [2.5.0] - 2023-09-05

### Added

* Units definition file at `data/units.txt`
* Quantity conversion for `z` parameter of `make`, which makes it possible to
  use `make` with pure Python inputs

### Changed

* Get unit registry from application and add Joseki required units by loading
  a units definition file.
* Alias `ppm` in `src/joseki/data/units.txt`

## [2.4.0] - 2023-08-07

*Yanked release*

## [2.3.0] - 2023-07-20

*Yanked release*

## [2.2.0] - 2023-07-18

*Yanked release*

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
