---
tags:
    - Api
    - Code-generation
---

# get_indexed_jacobian

`#!python get_indexed_jacobian(use_dedt=False, use_cse=True, cse_var="cse")`

Computes the analytical Jacobian matrix for the chemical network $\left(\dfrac{\partial f_i}{\partial y_j}\right)$ using symbolic differentiation and optional CSE.

**Parameters**

**use_dedt** : _bool, optional_
: Include energy equation row. Default `False`.

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**Returns**

_IndexedReturn_
: `expressions` contains `IndexedValue` objects with 2D indices `[i, j]`.
