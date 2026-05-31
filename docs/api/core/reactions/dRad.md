---
tags:
    - Api
    - Reaction
---

# dRad

`#!python dRad()`

Returns the extra photon absorption/emission rate contribution expression for every reaction in the catalogue. This term feeds into the radiation moment equations; it is non-zero only for reactions with a radiation component. One entry per reaction, in catalogue order.

**Returns**

_Vector\[sympy.Basic\]_
: SymPy expression for the radiation energy density rate contribution for each reaction, in the same order as the catalogue.
