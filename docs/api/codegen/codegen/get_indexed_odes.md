---
tags:
    - Api
    - Code-generation
---

# get_indexed_odes

`#!python get_indexed_odes(use_cse=True, cse_var="cse")`

Generates ODE expressions with optional CSE, applied globally across the full ODE system.

**Parameters**

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**Returns**

_IndexedReturn_
: `{"extras": {"cse": IndexedList}, "expressions": IndexedList}`.
