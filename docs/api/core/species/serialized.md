---
tags:
    - Api
    - Species
---

# serialized

`#!python serialized(ne=False)`

Returns the canonical serialized key (`"/".join(sorted(exploded))`) for every species in the collection, in catalogue order. Isomers share the same serialized key, making these strings suitable for isomer-insensitive comparison. Pass `ne=True` to drop the electron species `"e-"`.

**Parameters**

**ne** : _bool, optional_
: If `True`, excludes the electron species `"e-"` from the returned vector. Default `False`.

**Returns**

_Vector\[str\]_
: Canonical serialized key for each species, in catalogue order.
