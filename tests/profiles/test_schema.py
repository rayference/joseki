from joseki import unit_registry as ureg
from joseki.profiles.schema import schema

def test_convert_no_n():
    """convert() adds 'n' data variable if missing in input"""
    converted = schema.convert(
        data_vars={
            "p": [1e5, 1e4, 1e3] * ureg.pascal,
            "t": [280, 260, 240] * ureg.kelvin,
            "x_N2": [0.78, 0.78, 0.78] * ureg.dimensionless,
        },
        coords={
            "z": [0, 10, 20] * ureg.km,
        },
        attrs={
        "Conventions": "CF-1.10",
        "title": "test",
        "institution": "test",
        "source": "test",
        "history": "test",
        "references": "test",
        "url": "test",
        "urldate": "test",
    }
    )
    assert "n" in converted
