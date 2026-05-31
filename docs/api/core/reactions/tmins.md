---
tags:
    - Api
    - Reaction
---

# tmins

`#!python tmins()`

Returns the minimum valid gas temperature for every reaction in the catalogue, in catalogue order. Reactions without a lower bound yield `None`.

**Returns**

_Vector\[float or None\]_
: Lower temperature bound in Kelvin for each reaction, or `None` when no lower bound is defined. One entry per reaction, in catalogue order.
