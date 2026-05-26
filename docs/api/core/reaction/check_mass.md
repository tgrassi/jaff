---
tags:
    - Api
    - Reaction
---

# check_mass

`#!python check_mass()`

Returns `True` if mass is conserved within one electron mass tolerance (9.1093837e-28 g). The tolerance accommodates reactions that appear to gain or lose a single electron mass due to ionisation, since the electron mass is negligible for chemistry purposes.

**Returns**

_bool_
: `True` if the reactant–product mass difference is less than 9.1093837e-28 g.
