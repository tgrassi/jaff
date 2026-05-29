---
tags:
    - Api
    - Species
---

# latex

`#!python latex(dollars=True, ne=False)`

Returns a LaTeX-formatted string for every species in the collection, in catalogue order. By default each string is wrapped in `$...$` so it renders inline in documents. Pass `ne=True` to drop the electron species `"e-"`.

**Parameters**

**dollars** : _bool, optional_
: If `True` (default), wraps each LaTeX string in `$...$` for inline rendering.

**ne** : _bool, optional_
: If `True`, excludes the electron species `"e-"` from the returned vector. Default `False`.

**Returns**

_Vector[str]_
: LaTeX-formatted string for each species, in catalogue order.
