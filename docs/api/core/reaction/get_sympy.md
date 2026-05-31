---
tags:
    - Api
    - Reaction
---

# get_sympy

`#!python get_sympy()`

Returns the symbolic rate-coefficient expression as a SymPy object. This is the same object stored in `Reaction.rate` and can be passed directly to SymPy's codegen or differentiation routines.

**Returns**

_sympy.Basic_
: Symbolic rate-coefficient expression for this reaction.
