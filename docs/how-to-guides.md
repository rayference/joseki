# How-to guides

## Quickstart

The main interface of *Joseki* is its [make](reference.md#src.joseki.core.make) 
method.
This method creates the atmospheric profile corresponding to a given identifier.
For example, make the so-called *AFGL US Standard* atmospheric profile from 
[Anderson et al (1986)](bibliography.md#Anderson+1986) with:

```python
import joseki

ds = joseki.make(identifier="afgl_1986-us_standard")
```


Display the available identifiers with:

```python
joseki.identifiers()
```

Use the [`to_netcdf`](https://docs.xarray.dev/en/stable/generated/xarray.Dataset.to_netcdf.html)
method to save the dataset to the disk as a 
[netCDF](https://www.unidata.ucar.edu/software/netcdf/) file:

```python
ds.to_netcdf("my_dataset.nc")
```

For other formats, refer to the 
[xarray IO documentation](https://docs.xarray.dev/en/stable/user-guide/io.html).

??? example "Saving to CSV file"

    ```python
    ds.to_dataframe().to_csv("my_dataset.csv")
    ```

    Note that one drawback of saving to a CSV file in the above manner is that
    the information on the quantity units is lost.

Open the dataset again using 
[`open_dataset`](reference.md#src.joseki.core.open_dataset):

```python
ds = joseki.open_dataset("my_dataset.nc")
```

The datasets format is described [here](explanation.md#data-set-format).

## Altitude grid

You can specify the altitude grid for your atmospheric profile. If the source
atmospheric profile is based on tabulated data, it is going to be interpolated
on the specified altitude grid.

??? example "Example"

    ```python
    import numpy as np

    from joseki.units import ureg


    ds = joseki.make(
        identifier="afgl_1986-us_standard",
        z=np.linspace(0, 100, 51) * ureg.km,
    )
    ```

During interpolation, the column number densities associated to the different
atmospheric constituents are likely going to be changed.
In the example above, the ozone column number density is increased to 
346.60 Dobson units compared to the atmospheric profile with the original
altitude grid, which has an ozone column number density of 345.75 Dobson units.
To ensure column densities are conserved during interpolation, set the 
`conserve_column` parameter to `True`.

??? example "Example"

    ```python
    ds = joseki.make(
        identifier="afgl_1986-us_standard",
        z=np.linspace(0, 100, 51) * ureg.km,
        conserve_column=True,
    )
    ```
## Cells representation

To make an atmospheric profile where data variables are given in altitude cells
instead of at altitude levels, set the parameter `represent_in_cells` to
`True`:

```python
ds = joseki.make(
    identifier="afgl_1986-us_standard",
    represent_in_cells=True,
)
```

The resulting dataset has a coordinate variable `z` that corresponds to
the altitude cells center and a data variable `z_bounds` that indicate the
altitude bounds of each altitude cell, i.e. atmospheric layer.

Note that moving a profile from the nodes-representation to the 
cells-representation is achieved by interpolating the nodes-represented profile.
As a result, column densities are likely to be different in the 
cells-represented profile.

Similarly to [when specifying the altitude grid](#altitude-grid), you can 
ensure that column densities are conserved with the `conserve_column` parameter.

## Advanced options

The collection of atmospheric profiles defined by
[Anderson et al (1986)](bibliography.md#Anderson+1986) includes volume mixing
ratio data for 28 molecules, where molecules 8-28 are described as *additional*.
By default, these additional molecules are included in the atmospheric profile.
To discard these additional molecules, set the `additional_molecules`
parameter to `False`:

```python
ds = joseki.make(
    identifier="afgl_1986-us_standard",
    represent_in_cells=True,
    additional_molecules=False,
)
```

The resulting dataset now includes only 7 molecules, instead of 28.

## Derived quantities

You can compute various derived quantities from a thermophysical properties
dataset produced by `joseki`, as illustrated by the examples below.

??? example "Column number density"

    ```python
    ds = joseki.make(identifier="afgl_1986-us_standard")
    ds.joseki.column_number_density["O3"].to("dobson_unit")
    ```
  
??? example "Column mass density"

    ```python
    ds.joseki.column_mass_density["H2O"]
    ```

??? example "Number density at sea level"

    ```python
    ds.joseki.number_density_at_sea_level["CO2"]
    ``` 

??? example "Mass density at sea level"

    ```python
    ds.joseki.mass_density_at_sea_level["CH4"]
    ```

For further details on these methods, refer to the [API reference](reference.md).

### Rescaling

You can modify the amount of a given set of molecules in your thermophysical
properties dataset by applying a 
[rescale](reference.md#src.joseki.accessor.JosekiAccessor.rescale) 
transformation.

!!! example "Example"

    ```python
    ds = joseki.make(identifier="afgl_1986-us_standard")
    rescaled = ds.joseki.rescale(
       factors={
          "H2O": 0.5,
          "CO2": 1.5,
          "CH4": 1.1,
       }
    )
    ```

In the example above, the amount of water vapor is halfed whereas the amount of
carbon dioxide and methane is increased by 150% and 110%, respectively.
When a rescale transformation has been applied to a dataset, its ``history`` 
attribute is updated to indicate what scaling factors were applied to what 
molecules.


### Plotting

!!! note "Note"

    For plotting, you will need to install the
    [matplotlib library](https://matplotlib.org).

You can easily make a plot of any of the variables of a dataset, i.e.,
air pressure (``p``), air temperature (``t``), air number density (``n``) or
volume fraction (``x_*``):

??? example "Pressure plot"

    ``` python
    import matplotlib.pyplot as plt 

    ds = joseki.make(
       identifier="afgl_1986-us_standard",
       additional_molecules=False
    )

    ds.p.plot(
       figsize=(4, 8),
       ls="dotted",
       marker=".",
       y="z",
       xscale="log",
    )
    plt.show()
    ```

    ![image](fig/user_guide/plotting-p.png)

??? example "Temperature plot"

    ```python
    ds.t.plot(
       figsize=(4, 8),
       ls="dotted",
       marker=".",
       y="z",
       xscale="linear",
    )
    plt.show()
    ```

    ![image](fig/user_guide/plotting-t.png)

??? example "Number density plot"

    ```python
    ds.n.plot(
       figsize=(4, 8),
       ls="dotted",
       marker=".",
       y="z",
       xscale="log",
    )
    plt.show()
    ```

    ![image](fig/user_guide/plotting-n.png)


??? example "Volume fraction plot"

    ```python
    plt.figure(figsize=(8, 8)) 

    for m in ds.joseki.molecules:
       ds[f"x_{m}"].plot(
          ls="dotted",
          marker=".",
          y="z",
          xscale="log",
       )

    plt.xlabel("volume fraction [dimensionless]")
    plt.legend(ds.joseki.molecules)
    plt.show()
    ```

    ![image](fig/user_guide/plotting-x.png)
