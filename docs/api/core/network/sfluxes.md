---
tags:
    - Api
    - Network
---

# sfluxes

`#!python sfluxes()`

Returns symbolic flux expressions for all reactions. The flux of a reaction is given by

<!-- prettier-ignore -->
$$ k \times \prod_{i=1}^{N}[R_i]^{\alpha_i} $$

where $k$ is the reaction rate coefficient, $R_i$ is the reactant concentration, and $\alpha_i$ is its stoichiometric ratio.

**Returns**

_list of sympy.Expr_
: One flux expression per reaction.
