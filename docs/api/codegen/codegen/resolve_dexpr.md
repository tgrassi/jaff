---
tags:
    - Api
    - Code-generation
---

# resolve_dexpr

`#!python resolve_dexpr(expr, species_var="y", brac_format="")`

Resolves a symbolic expression involving SymPy `Derivative` objects into language-specific code by substituting species array references.

**Parameters**

**expr** : _sympy.Basic_
: Expression to resolve.

**species_var** : _str, optional_
: Species array variable name. Default `"y"`.

**brac_format** : _str, optional_
: Override bracket style. Default `""`.

**Returns**

_str_
: Resolved expression as a code string.
