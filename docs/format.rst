.. _format:

Data set format
===============

Joseki produces atmospheric profile data sets in the
`NetCDF format <https://www.unidata.ucar.edu/software/netcdf/>`_ using the
`xarray library <http://xarray.pydata.org/en/stable/>`_ which provides a
comprehensive, robust and convenient interface to read, write, manipulate and
visualise NetCDF data.

Metadata conventions
--------------------

The NetCDF format allows to store metadata alongside data.
Joseki's data sets metadata follow the
`conventions for Climate and Forecast (v1.8) <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html>`_.

Standard names
~~~~~~~~~~~~~~

The Climate and Forecast (CF) conventions define standard names to describe
variables.
Joseki's data sets complies with
`CF Standard Name Table Version 77, 19 January 2021 <http://cfconventions.org/Data/cf-standard-names/77/build/cf-standard-name-table.html>`_,
except for the following variables for which a standard name did not exist
in the table and was derived:

.. list-table:: Derived standard names
   :widths: 35 35 15
   :header-rows: 1

   * - Standard name
     - Long name
     - Units
   * - ``air_number_density``
     - ``air number density``
     - ``m^-3``
   * - ``volume_fraction``
     - ``volume fraction``
     - ``dimensionless``
   * - ``layer_center_altitude``
     - ``layer center altitude``
     - ``km``

Structure
---------

The data set includes 3+ data variables:

.. list-table:: Data variables
   :widths: 35 35 5 15
   :header-rows: 1

   * - Standard name
     - Long name
     - Symbol
     - Units
   * - ``air_pressure``
     - ``air pressure``
     - ``p``
     - ``Pa``
   * - ``air_temperature``
     - ``air temperature``
     - ``t``
     - ``K``
   * - ``air_number_density``
     - ``air number density``
     - ``n``
     - ``m^-3``
   * - ``volume_fraction``
     - ``volume fraction``
     - ``x_<m>``
     - ``dimensionless``

where ``<m>`` is the chemical formula of the given molecule, and two
coordinates variables (``altitude`` and ``layer_center_altitude``
exclude each other):

.. list-table:: Coordinate variables
   :widths: 35 35 5 15
   :header-rows: 1

   * - Standard name
     - Long name
     - Symbol
     - Units
   * - ``altitude``
     - ``altitude``
     - ``z``
     - ``km``
   * - ``layer_center_altitude``
     - ``layer center altitude``
     - ``z``
     - ``km``
   * - ``molecule``
     - ``molecule``
     - ``m``
     -

All data variables depend solely on the altitude (either ``altitude`` or
``layer_center_altitude``).
