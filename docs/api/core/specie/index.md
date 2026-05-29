---
tags:
    - Api
    - Species
---

# Specie

`jaff.core.species.Specie`

The `Specie` class represents a single chemical species — atom, molecule, ion, or grain. It parses the species name to determine elemental composition, total mass, net charge, and LaTeX formatting.

## Constructor

`#!python Specie(name, index=0)`

**Parameters**

**name** : _str_
: Chemical name (e.g. `"H2O"`, `"HCO+"`, `"e-"`). Electron must be `"e-"`.

**index** : _int, optional_
: Position in the network species list. This is not required when instantiating an independent specie. Default `0`.

## Attributes

| Attribute    | Type            | Description                                                                                                                                |
| ------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `name`       | `str`           | Species name as it appears in the network file (e.g. `"H2O+"`, `"e-"`)                                                                     |
| `mass`       | `float or None` | Total mass in grams (CGS), summed over constituent atoms                                                                                   |
| `charge`     | `int`           | Net charge in units of elementary charge. Trailing `"+"` / `"-"` characters are counted; `"e-"` is always `−1`                             |
| `index`      | `int`           | Position of this species in the parent `Species` catalogue                                                                                 |
| `exploded`   | `list[str]`     | Sorted list of atomic symbols with repetition (e.g. `["H", "H", "O"]` for H2O). Charge tokens `"+"` / `"-"` are included                   |
| `fidx`       | `str`           | Flat index identifier safe for generated C/Fortran/Python source. `"+"` → `"j"`, `"-"` → `"k"`. H2O+ → `"idx_h2oj"`. Electrons → `"idx_e"` |
| `serialized` | `str`           | Canonical form: `"/".join(sorted(exploded))`. Isomers share the same serialized form (e.g. HCO+ and HOC+ both → `"+/C/H/O"`)               |
| `elements`   | `Elements`      | [`Elements`](../elements/index.md) collection for this single specie                                                                       |
