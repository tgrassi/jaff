---
tags:
    - Api
    - Reaction
---

# serialize_exploded

`#!python serialize_exploded()`

Builds the atom-level serialized form (isomer-insensitive). Each species is replaced by its `Specie.serialized` form (e.g. H2O+ → `"+/H/H/O"`), then species tokens are sorted and joined with `"_"`. Reactants and products are separated by `"__"`.

**Returns**

_str_
: Atom-level canonical key, e.g. `"+/H/H/O__H/H/O_Hj"` for a reaction involving H2O+.
