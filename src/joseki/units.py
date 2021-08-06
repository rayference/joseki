"""Units module."""
import pint

ureg = pint.UnitRegistry()

# define ppmv unit
ureg.define("ppmv = 1e-6 * m^3 / m^3")
