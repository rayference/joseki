Data format
===========

Joseki produces atmospheric profile datasets in the
`NetCDF format <https://www.unidata.ucar.edu/software/netcdf/>`_ using the
`xarray library <http://xarray.pydata.org/en/stable/>`_ which provides a
comprehensive, robust and convenient interface to read, write, manipulate and
visualize NetCDF data.

Metadata conventions
--------------------

The NetCDF format allows storing metadata alongside data.
Joseki's dataset metadata follows the
`conventions for Climate and Forecast (v1.10) <https://cfconventions.org/Data/cf-conventions/cf-conventions-1.10/cf-conventions.html>`_.

Standard names
--------------

The Climate and Forecast (CF) conventions define standard names to describe
variables.
Joseki's datasets comply with
`CF Standard Name Table Version 81, 25 April 2023 <https://cfconventions.org/Data/cf-standard-names/81/build/cf-standard-name-table.html>`_
except for the following variables for which a standard name did not exist
(hence we derived one):

.. list-table::
    :widths: 40 40 20
    :header-rows: 1

    - * Standard name
      * Long name
      * Units

    - * ``air_number_density``
      * ``air number density``
      * ``m^-3``

Structure
---------

A dataset includes 4+ data variables:

.. list-table::
    :widths: 35 35 10 20
    :header-rows: 1

    - * Standard name
      * Long name
      * Symbol
      * Units

    - * ``air_pressure``
      * ``air pressure``
      * ``p``
      * ``Pa``

    - * ``air_temperature``
      * ``air temperature``
      * ``t``
      * ``K``

    - * ``air_number_density``
      * ``air number density``
      * ``n``
      * ``m^-3``

    - * ``mole_fraction_of_M_in_air``
      * ``mole fraction of M in air``
      * ``x_M``
      * ``dimensionless``

where ``M`` is the chemical formula of the given molecule (*e.g.*
``mole_fraction_of_H2O_in_air`` is associated with the symbol ``x_H2O``), and one of
the two following coordinate variables:

.. list-table::
    :widths: 35 35 10 20
    :header-rows: 1

    - * Standard name
      * Long name
      * Symbol
      * Units

    - * ``altitude``
      * ``altitude``
      * ``z``
      * ``km``

    - * ``layer_center_altitude``
      * ``layer center altitude``
      * ``z``
      * ``km``

All data variables depend solely on the altitude (either ``altitude`` or
``layer_center_altitude``).
