---
tags:
    - Api
    - Species
---

# normalized_names

`#!python normalized_names()`

Returns a normalized identifier string for every species in the collection, in catalogue order. Each name is lowercased and has `"+"` replaced by `"p"` and `"-"` replaced by `"n"`, producing strings that are valid variable names in C, Fortran, and Python. For example `"HCO+"` becomes `"hcop"` and `"e-"` becomes `"en"`.

**Returns**

_Vector[str]_
: Normalized, code-safe identifier string for each species, in catalogue order.
