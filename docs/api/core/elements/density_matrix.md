---
tags:
    - Api
    - Elements
---

# density_matrix

`#!python density_matrix()`

Atom-count matrix (stoichiometric composition matrix). Entry `[i][j]` is the number of atoms of element `i` in species `j` (e.g. H in H2O is 2).

**Returns**

_list[list[int]]_
: Shape `(n_elements, n_species)`.

**Example**

For elements `['C','H','O']` and species `['CO','H2O','CH4']`:

```
[[1, 0, 1],  # C: 1 in CO, 0 in H2O, 1 in CH4
 [0, 2, 4],  # H: 0 in CO, 2 in H2O, 4 in CH4
 [1, 1, 0]]  # O: 1 in CO, 1 in H2O, 0 in CH4
```
