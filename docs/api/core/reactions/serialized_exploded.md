---
tags:
    - Api
    - Reaction
---

# serialized_exploded

`#!python serialized_exploded()`

Returns the atom-level (isomer-insensitive) canonical key for every reaction in the catalogue, in catalogue order. Because these keys are built from `Specie.serialized` forms, two reactions that differ only in isomers (e.g. HCO+ vs HOC+) will share the same key.

**Returns**

_Vector[str]_
: Atom-level canonical keys built from `Specie.serialized` forms for each reaction, in the same order as the catalogue.
