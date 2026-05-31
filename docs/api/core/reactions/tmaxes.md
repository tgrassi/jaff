---
tags:
    - Api
    - Reaction
---

# tmaxes

`#!python tmaxes()`

Returns the maximum valid gas temperature for every reaction in the catalogue, in catalogue order. Reactions without an upper bound yield `None`.

**Returns**

_Vector\[float or None\]_
: Upper temperature bound in Kelvin for each reaction, or `None` when no upper bound is defined. One entry per reaction, in catalogue order.
