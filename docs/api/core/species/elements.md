---
tags:
    - Api
    - Species
---

# elements

`#!python elements(ne=False)`

Returns an [`Elements`](../elements/index.md) catalogue for every species in the collection, in catalogue order. Each `Elements` instance lists the unique chemical elements present in the corresponding species and is used to build composition matrices. Pass `ne=True` to drop the electron species `"e-"`.

**Parameters**

**ne** : _bool, optional_
: If `True`, excludes the electron species `"e-"` from the returned vector. Default `False`.

**Returns**

_Vector[Elements]_
: `Elements` catalogue for each species, in catalogue order.
