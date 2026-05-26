---
tags:
    - Api
    - Code-generation
---

# get_indexed_ode_expressions

`#!python get_indexed_ode_expressions()`

Generates ODE expressions (sum of flux contributions) for each species, without CSE.

**Returns**

_IndexedList_
: Each `IndexedValue` has `indices=[i]` and `value=ode_expression_string`.
