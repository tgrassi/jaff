---
tags:
    - Api
    - Elements
---

# get_list

`#!python get_list()`

Returns the sorted list of `Element` objects derived from the species provided at construction. The order follows alphabetical sort on element symbol, which matches the row order of the composition matrices (`truth_matrix`, `density_matrix`).

**Returns**

_list\[Element\]_
: All unique `Element` objects, sorted alphabetically by chemical symbol.
