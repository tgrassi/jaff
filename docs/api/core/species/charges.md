---
tags:
    - Api
    - Species
---

# charges

`#!python charges(ne=False)`

Returns the net charge (in units of elementary charge) for every species in the collection, in catalogue order. The charge is derived by counting trailing `"+"` and `"-"` tokens in the species name; `"e-"` is always `−1`. Pass `ne=True` to drop the electron species.

**Parameters**

**ne** : _bool, optional_
: If `True`, excludes the electron species `"e-"` from the returned vector. Default `False`.

**Returns**

_Vector\[int\]_
: Net charge in units of elementary charge for each species, in catalogue order.
