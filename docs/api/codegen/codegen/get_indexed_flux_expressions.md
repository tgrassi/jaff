---
tags:
    - Api
    - Code-generation
---

# get_indexed_flux_expressions

`#!python get_indexed_flux_expressions()`

Generates flux expressions for all reactions as `IndexedValue` objects. The flux of a reaction is given by

<!-- prettier-ignore -->
$$ k \times \prod_{i=1}^{N}[R_i]^{\alpha_i} $$

where $k$ is the reaction rate coefficient, \[$R_i$\] is the reactant concentration and $\alpha_i$ is its stoichiometric ratio. If the photo-reaction rate is unknown, the `$IDX$` argument is supplied as a placeholder for the photo-reaction index.

**Returns**

_IndexedList_
: Each `IndexedValue` has `indices=[i]` and `value=flux_expression_string`.
