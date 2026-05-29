---
tags:
    - Api
    - Species
---

# exploded

`#!python exploded(ne=False)`

Returns the sorted atomic-symbol list (with repetition) for every species in the collection, in catalogue order. For example, H2O yields `["H", "H", "O"]`. Charge tokens (`"+"`, `"-"`) are included. Pass `ne=True` to drop the electron species `"e-"`.

**Parameters**

**ne** : _bool, optional_
: If `True`, excludes the electron species `"e-"` from the returned vector. Default `False`.

**Returns**

_Vector[list[str]]_
: Sorted atomic-symbol list (with repetition) for each species, in catalogue order.
