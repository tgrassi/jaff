---
tags:
    - Api
    - Code-generation
---

# get_indexed_rates

`#!python get_indexed_rates(use_cse=True, cse_var="x")`

Generates rate coefficient expressions as `IndexedValue` objects with optional CSE. Photo-reactions and string rates are excluded from CSE.

**Parameters**

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: Prefix for CSE temporary variable names. Default `"x"`.

**Returns**

_IndexedReturn_
: `{"extras": {"cse": IndexedList}, "expressions": IndexedList}`. Each `IndexedValue` in `expressions` has `indices=[i]` and `value=rate_code_string`.
