---
tags:
    - Api
    - Species
---

# masses

`#!python masses(ne=False)`

Returns the total mass in grams (CGS) for every species in the collection, summed over constituent atoms. Species whose composition cannot be resolved yield `None`. Pass `ne=True` to drop the electron species `"e-"`.

**Parameters**

**ne** : _bool, optional_
: If `True`, excludes the electron species `"e-"` from the returned vector. Default `False`.

**Returns**

_Vector[float or None]_
: Total mass in grams (CGS) for each species, or `None` when the mass cannot be resolved. One entry per species, in catalogue order.
