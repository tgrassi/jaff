---
tags:
    - Api
    - Code-generation
---

# get_indexed_flux_expressions

`#!python get_indexed_flux_expressions()`

Generates flux expressions (rate \* prod(reactant_densities)) for all reactions as `IndexedValue` objects. Flux expressions contain the template placeholder `$IDX$` for the reaction index.

**Returns**

_IndexedList_
: Each `IndexedValue` has `indices=[i]` and `value=flux_expression_string`.
