---
tags:
    - Api
    - Species
---

# names

`#!python names(ne=False)`

Returns the name string of every species in the collection, in the order they were added. Pass `ne=True` to drop the electron species `"e-"` from the result, which is useful when building solver state vectors that treat electrons separately.

**Parameters**

**ne** : _bool, optional_
: If `True`, excludes the electron species `"e-"` from the returned vector. Default `False`.

**Returns**

_Vector[str]_
: Name of each species in the collection, in catalogue order.
