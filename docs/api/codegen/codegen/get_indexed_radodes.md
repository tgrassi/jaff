---
tags:
    - Api
    - Code-generation
---

# get_indexed_radodes

`#!python get_indexed_radodes(order=0, use_cse=True, cse_var="cse")`

Generates radiation ODE expressions for the given moment order.

**Parameters**

**order** : _int, optional_
: Radiation moment order. Default `0`.

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**Returns**

_IndexedReturn_
: Radiation ODE expressions as indexed values.
