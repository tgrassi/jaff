---
tags:
    - Api
    - Reaction
---

# serialize

`#!python serialize()`

Builds the name-level serialized form (isomer-sensitive). Species names are sorted alphabetically and joined with `"."`. Reactants and products are separated by `"__"`. (The `"."` joiner — not `"_"` — is used because special pseudo-species names start with `_`.)

**Returns**

_str_
: Name-level canonical key, e.g. `"H.H2O+__H+.H2O"` for `H + H2O+ -> H2O + H+`.
