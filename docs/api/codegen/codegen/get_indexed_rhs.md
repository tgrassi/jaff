---
tags:
    - Api
    - Code-generation
---

# get_indexed_rhs

`#!python get_indexed_rhs(use_cse=True, cse_var="cse")`

Generates the full right-hand side including the energy equation as the last element. Radiation equations are appended after the internal energy equation if radiation codegen is enabled.

**Parameters**

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**Returns**

_IndexedReturn_
: `expressions` contains `n_species + 1` entries; the last is the energy equation.
