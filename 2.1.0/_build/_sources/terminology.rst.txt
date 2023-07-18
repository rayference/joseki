.. _terminology:

Terminology
===========

Column number density
---------------------

If :math:`n_{\mathrm{M}} (z)` denotes the number density of molecule M at altitude
:math:`z`, then the column number density of molecule M is

.. math::

   N_{\mathrm{M}} = \int_{0}^{+\infty} n_{\mathrm{M}} (z) \, \mathrm{d} z

Column number density has dimensions of ``length^-2``.

Column mass density
-------------------

The column mass density is to mass density what column number density is to
number density, i.e.,

.. math::

   P_{\mathrm{M}} = \int_{0}^{+\infty} \rho_{\mathrm{M}} (z) \, \mathrm{d} z

where :math:`\rho_{\mathrm{M}} (z)` is the mass density of molecule M at
altitude :math:`z`.

Mass density is related with number density through:

.. math::

   \rho_{\mathrm{M}} = m_{\mathrm{M}} \, n_{\mathrm{M}}

where :math:`m_{\mathrm{M}}` is the molecular mass.

Since molecular mass does not change with altitude, we simply have

.. math::

   P_{\mathrm{M}} = m_{\mathrm{M}} \, N_{\mathrm{M}}

Column mass density has dimensions of ``mass * length^-2``.

Number density at sea level
---------------------------

Sea level is defined by :math:`z=0`, hence the number density at sea level of molecule
M is simply :math:`n_{\mathrm{M}}(0)`.

Number density at sea level has dimensions of ``length^-3``.

Mass density at sea level
-------------------------

Similarly, mass density at sea level is
:math:`\rho_{\mathrm{M}}(0) = m_{\mathrm{M}} \, n_{\mathrm{M}}(0)`.

Mass density at sea level has dimensions of ``mass * length^-3``.
