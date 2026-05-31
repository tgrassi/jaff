---
tags:
    - Api
    - Reaction
---

# rates

`#!python rates()`

Returns the symbolic rate-coefficient expression for every reaction in the catalogue, in catalogue order. Units depend on reaction order (e.g. cm³ s⁻¹ for two-body reactions).

**Returns**

_Vector\[sympy.Basic\]_
: SymPy rate-coefficient expression for each reaction, in the same order as the catalogue.
