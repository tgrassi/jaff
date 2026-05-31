---
tags:
    - Api
    - Code-generation
---

# get_indexed_ode_expressions

`#!python get_indexed_ode_expressions()`

Generates ODE expressions (sum of flux contributions) for each species, without CSE. The rate of change of a species concentration is given by

<!-- prettier-ignore -->
$$ \frac{dn}{dt} = \sum_{i = 1}^{N}(-1)^a f_i\begin{cases} &  a = 0 \text{ when } n \text{ is a product} \\ & a = 1 \text{ when } n \text{ is a reactant} \end{cases} $$

where $f_i$ is the flux of reaction $i$.

**Returns**

_IndexedList_
: Each `IndexedValue` has `indices=[i]` and `value=ode_expression_string`.
