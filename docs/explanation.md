## Terminology

### Column number density

If $n_{\mathrm{M}} (z)$ denotes the number density of molecule M at altitude
$z$, then the column number density of molecule M is

$$
N_{\mathrm{M}} = \int_{0}^{+\infty} n_{\mathrm{M}} (z) \, \mathrm{d} z
$$

Column number density has dimensions of `length^-2`.

### Column mass density

The column mass density is to mass density what column number density is to
number density, i.e.,

$$
P_{\mathrm{M}} = \int_{0}^{+\infty} \rho_{\mathrm{M}} (z) \, \mathrm{d} z
$$

where $\rho_{\mathrm{M}} (z)$ is the mass density of molecule M at
altitude $z$.

Mass density is related with number density through:

$$
\rho_{\mathrm{M}} = m_{\mathrm{M}} \, n_{\mathrm{M}}
$$

where $\mathrm{M}$ is the molecular mass.

Since molecular mass does not change with altitude, we simply have

$$
P_{\mathrm{M}} = m_{\mathrm{M}} \, N_{\mathrm{M}}
$$

Column mass density has dimensions of `mass * length^-2`.

### Number density at sea level

Sea level is defined by $z=0$, hence the number density at sea level of molecule
M is simply $n_{\mathrm{M}}(0)$.
Number density at sea level has dimensions of `length^-3`.

### Mass density at sea level

Similarly, mass density at sea level is
$\rho_{\mathrm{M}}(0) = m_{\mathrm{M}} \, n_{\mathrm{M}}(0)$.
Mass density at sea level has dimensions of `mass * length^-3`.


## Dataset schema

Joseki produces atmospheric profile datasets in the
[NetCDF format](https://www.unidata.ucar.edu/software/netcdf/) using the
[xarray library](http://xarray.pydata.org/en/stable/) which provides a
comprehensive, robust and convenient interface to read, write, manipulate and
visualise NetCDF data.

### Metadata conventions

The NetCDF format allows to store metadata alongside data.
Joseki's datasets metadata follow the
[conventions for Climate and Forecast (v1.8)](http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html).

### Standard names

The Climate and Forecast (CF) conventions define standard names to describe
variables.
Joseki's datasets comply with
[CF Standard Name Table Version 77, 19 January 2021](http://cfconventions.org/Data/cf-standard-names/77/build/cf-standard-name-table.html),
except for the following variables for which a standard name did not exist
in the table and was derived:


| Standard name        | Long name            |      Units      |
| :------------------- | :------------------- | :-------------: |
| `air_number_density` | `air number density` |     `m^-3`      |
| `volume_fraction`    | `volume fraction`    | `dimensionless` |

### Structure

A dataset includes 4+ data variables:

| Standard name        | Long name            | Symbol  |      Units      |
| :------------------- | :------------------- | :-----: | :-------------: |
| `air_pressure`       | `air pressure`       |   `p`   |      `Pa`       |
| `air_temperature`    | `air temperature`    |   `t`   |       `K`       |
| `air_number_density` | `air number density` |   `n`   |     `m^-3`      |
| `volume_fraction`    | `volume fraction`    | `x_<m>` | `dimensionless` |

where `<m>` is the chemical formula of the given molecule, and one of the two
following coordinates variables:

| Standard name           | Long name               | Symbol | Units |
| :---------------------- | :---------------------- | :----: | :---: |
| `altitude`              | `altitude`              |  `z`   | `km`  |
| `layer_center_altitude` | `layer center altitude` |  `z`   | `km`  |

All data variables depend solely on the altitude (either ``altitude`` or
``layer_center_altitude``).
