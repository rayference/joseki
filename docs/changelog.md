## `2.1.0` (unreleased)

!!! help "Documentation"

    * Add installation instructions for conda


!!! success "Improvements"

    * Added all missing HITRAN species
    * Fix out-dated command-line interface
    * Add thin wrappers for `xarray.open_dataset` and `xarray.load_dataset`
    * Add convenience method to list available identifiers


!!! note "Internal Changes"

    * Lower version constraint on Numpy


## `2.0.0` (2023-02-14)

!!! help "Documentation"

    * Re-organise content
    * Move from Sphinx to [mkdocs](https://www.mkdocs.org/)


!!! success "Improvements"

    * Added a profile factory
    * Added profile dataset schema converter and validator
    * Added logging

!!! note "Internal Changes"

    * Move from Poetry to [PDM](https://pdm.fming.dev/)