---
tags:
    - Api
    - Elements
---

# truth_matrix

`#!python truth_matrix()`

Binary element-presence matrix. Entry `[i][j]` is `1` if element `i` is present at least once in species `j`, otherwise `0`.
Row order matches the sorted element list; column order matches the order of _species_ passed to `__init__`.
**Returns**

_list[list[int]]_
: Shape `(n_elements, n_species)`.

**Example**

For elements `['C','H','O']` and species `['CO','H2O','CH4']`:

```
[[1, 0, 1],  # C in CO and CH4
 [0, 1, 1],  # H in H2O and CH4
 [1, 1, 0]]  # O in CO and H2O
```
