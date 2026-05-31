---
tags:
    - Api
    - Network
---

# free_symbols

`#!python free_symbols(expr)`

Returns the set of free SymPy symbols in `expr`, excluding nden matrix entries.

**Parameters**

**expr** : _sympy.Basic_
: Expression to inspect.

**Returns**

_set\[sympy.Basic\]_
: Free symbols found in the expression, with `nden` matrix entries excluded.
