---
tags:
    - Api
    - Code-generation
---

# get_indexed_radodes

`#!python get_indexed_radodes(order=0, use_cse=True, cse_var="cse")`

Generates radiation ODE expressions in a given pattern

**Parameters**

**order** : _int, optional_
: Radiation list pattern which is ordered as:

| Order | Radiation list pattern                   |
| ----- | ---------------------------------------- |
| 0     | [$rd_0$, $f_0$, $rd_1$, $f_1$, ...]      |
| 1     | [$f_0$, $rd_0$, $f_1$, $rd_1$, ...]      |
| 2     | [$rd_0$, $rd_1$, ..., $f_0$, $f_1$, ...] |
| 3     | [$f_0$, $f_1$, ..., $rd_0$, $rd_1$, ...] |

Where $rd_i$ is the radiation energy density / photon density and $f_i$ is the radiation flux.

Default is `0`.

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**Returns**

_IndexedReturn_
: Radiation ODE expressions as indexed values.
