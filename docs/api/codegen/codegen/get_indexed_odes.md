---
tags:
    - Api
    - Code-generation
---

# get_indexed_odes

`#!python get_indexed_odes(use_cse=True, cse_var="cse")`

Generates ODE expressions with optional CSE, applied globally across the full ODE system. The rate of change of a species concentration is given by

<!-- prettier-ignore -->
$$ \frac{dn}{dt} = \sum_{i = 1}^{N}(-1)^a f_i\begin{cases} &  a = 0 \text{ when } n \text{ is a product} \\ & a = 1 \text{ when } n \text{ is a reactant} \end{cases} $$

where $f_i$ is the flux of reaction $i$.

**Parameters**

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**Returns**

_IndexedReturn_
: `{"extras": {"cse": IndexedList}, "expressions": IndexedList}`.
