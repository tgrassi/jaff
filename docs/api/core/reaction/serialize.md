---
tags:
    - Api
    - Reaction
---

# serialize

`#!python serialize()`

Builds the name-level serialized form (isomer-sensitive). Species names are sorted alphabetically and joined with `"_"`. Reactants and products are separated by `"__"`.

**Returns**

_str_
: Name-level canonical key, e.g. `"H_H2Oj__H2O_Hj"` for `H + H2O+ -> H2O + H+`.
