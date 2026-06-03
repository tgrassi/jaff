---
tags:
    - Api
---

# Units

`jaff.physics.units`

Unit registry, conversions, and the `Quantity` value object. Conversion factors
are sourced from `jaff.physics.constants` (the `cgs` set), so there is a single
source of truth and no duplicated magic numbers. All conversions are
numpy-elementwise: values may be floats or numpy arrays.

Within a physical dimension a conversion is a pure multiplicative ratio to that
dimension's CGS base unit. Conversions *between* dimensions
(wavelength / frequency / temperature ↔ energy) route through physics
**bridges**, because e.g. `E = h c / λ` is inverse in the wavelength and cannot
be a constant factor.

## convert

`#!python convert(value, from_unit, to_unit)`

Convert `value` from `from_unit` to `to_unit`. Works elementwise on floats or
numpy arrays.

**Parameters**

**value** : _float or numpy.ndarray (or list/tuple, coerced to a float array)_
: The numeric value(s) to convert.

**from_unit, to_unit** : _str_
: Registered unit names.

**Returns**

_float or numpy.ndarray_
: `value` expressed in `to_unit`.

**Raises**

**UnknownUnitError**
: If either unit name is not registered.

**IncompatibleUnitsError**
: If the units' dimensions differ and no bridge connects them.

```python
from jaff.physics import units

units.convert(13.605693, "eV", "Ry")   # 1.0
units.convert(1.0, "Mb", "cm2")         # 1e-18
units.convert(121.567, "nm", "eV")      # ≈ 10.19  (Lyman-α, via a bridge)
```

## Quantity

`#!python Quantity(value, unit)`

A `(value, unit)` pair with conversion, attribute access, and arithmetic.
Attribute access returns the value converted to the named unit. Addition and
subtraction require operands of the same dimension; multiplication and division
by a scalar preserve the unit; dividing two same-dimension quantities yields a
dimensionless float. Compound units (products of quantities) are out of scope.

| Member            | Description                                            |
| ----------------- | ------------------------------------------------------ |
| `value`           | The magnitude (float or numpy array)                   |
| `unit`            | The unit symbol the quantity is expressed in           |
| `dimension`       | The `Dimension` the quantity measures                  |
| `to(unit)`        | Return a new `Quantity` expressed in `unit`            |
| `q.<unit>`        | The value converted to `<unit>` (e.g. `q.eV`, `q.erg`) |

```python
q = units.Quantity(121.6, "nm")
q.to("angstrom").value                       # 1216.0
q.eV                                          # ≈ 10.1
(units.Quantity(1.0, "eV") + units.Quantity(1.0, "keV")).eV   # 1001.0
```

## Supported units

| Dimension     | Base unit | Units                                    |
| ------------- | --------- | ---------------------------------------- |
| Energy        | `erg`     | `erg`, `eV`, `keV`, `MeV`, `J`, `Ry`     |
| Length        | `cm`      | `cm`, `m`, `nm`, `angstrom`, `um`        |
| Area          | `cm2`     | `cm2`, `m2`, `barn`, `Mb`                |
| Time          | `s`       | `s`, `ms`, `us`, `ns`                    |
| Charge        | `esu`     | `esu`, `statC`, `C`                      |
| Mass          | `g`       | `g`, `kg`, `amu`, `m_e`, `m_p`           |
| Temperature   | `K`       | `K`                                      |
| Frequency     | `Hz`      | `Hz`                                     |

Cross-dimension **bridges** connect energy with length (`E = h c / λ`),
frequency (`E = h ν`), and temperature (`E = k_b T`).

## Errors

The units subsystem raises a small exception hierarchy from `jaff.errors`:

| Exception                  | Raised when                                                          |
| -------------------------- | ------------------------------------------------------------------- |
| `UnitsError`               | Base class for all unit errors                                      |
| `UnknownUnitError`         | A unit name is not in the registry                                  |
| `IncompatibleUnitsError`   | Two units' dimensions cannot be converted or combined (no bridge)   |
