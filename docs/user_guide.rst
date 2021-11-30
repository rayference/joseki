.. _user_guide:

User guide
==========

This user guide introduces you to the Python interface of Joseki.

Joseki also has a command-line interface.
If you wish to learn how to use it, refer to the :ref:`cli` page.

Quickstart
----------

Make an atmospheric profile using the function :meth:`joseki.make`.
Use its ``identifier`` parameter to specify the atmospheric profile.
For example, make the *AFGL (1986) tropical* atmospheric profile with:

.. code-block:: python

   import joseki

   ds = joseki.make(identifier="afgl_1986-tropical")


Display the available identifiers with:

.. code-block:: python

   [id.value for id in joseki.Identifier]


If you want, you can save the data set to the disk as a NETCDF file:

.. code-block:: python

   ds.to_netcdf("my_data_set.nc")

Open the data set again using :class:`xarray.open_dataset`:

.. code-block:: python

   import xarray as xr

   ds = xr.open_dataset("my_data_set.nc")

The data sets format is described :ref:`here <format>`.

Cells representation
--------------------

To make an atmospheric profile where data variables are given in altitude cells
instead of at altitude levels, set the parameter ``represent_in_cells`` to
``True``:

.. code-block:: python

   ds = joseki.make(
       identifier="afgl_1986-tropical",
       represent_in_cells=True,
   )

The resulting data set has a coordinate variable ``z`` that corresponds to
the altitude cells center and a data variable ``z_bounds`` that indicate the
altitude bounds of each altitude cell, i.e. atmospheric layer.

Advanced options
----------------

The collection of atmospheric profiles defined by
:cite:`Anderson1986AtmosphericConstituentProfiles` includes volume mixing
ratio data for 28 molecules, where molecules 8-28 are described as *additional*.
By default, these additional molecules are included in the atmospheric profile.
To discard these additional molecules, set the ``additional_molecules``
parameter to ``False``:

.. code-block:: python

   ds = joseki.make(
       identifier="afgl_1986-tropical",
       represent_in_cells=True,
       additional_molecules=False,
   )

The resulting data set now includes only 7 molecules, instead of 28.
