---
tags:
    - Api
    - Network
---

# sodes

`#!python sodes()`

Returns symbolic ODE right-hand side expressions for all species. The rate of change of a specie concentration is given by

<!-- prettier-ignore -->
$$ \frac{dn}{dt} = \sum_{i} (-1)^a f_i\begin{cases} &  a = 0 \text{ when } n \text{ is a product} \\ & a = 1 \text{ when } n \text{ is a reaction} \end{cases} $$

**Returns**

_list of sympy.Basic_
: One dn/dt expression per specie.
