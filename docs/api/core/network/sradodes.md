---
tags:
    - Api
    - Network
---

# sradodes

`#!python sradodes(order=0)`

Returns symbolic radiation ODE expressions in a given pattern

**Parameters**

**order** : _int, optional_
: Radiation list pattern which is ordered as:

| Order | Radiation list pattern                   |
| ----- | ---------------------------------------- |
| 0     | \[$rd_0$, $f_0$, $rd_1$, $f_1$, ...\]      |
| 1     | \[$f_0$, $rd_0$, $f_1$, $rd_1$, ...\]      |
| 2     | \[$rd_0$, $rd_1$, ..., $f_0$, $f_1$, ...\] |
| 3     | \[$f_0$, $f_1$, ..., $rd_0$, $rd_1$, ...\] |

Where $rd_i$ is the radiation energy density / photon density and $f_i$ and is the radiation flux

Default is `0`.

**Returns**

_list of sympy.Expr_
: One expression per radiation band.
