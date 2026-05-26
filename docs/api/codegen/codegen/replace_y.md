---
tags:
    - Api
    - Code-generation
---

# replace_y

`#!python replace_y(expr, species_var="y", idx_prefix="", brac_format="", idx_offset=-1)`

Substitutes SymPy `nden[i]` matrix symbols with language-specific species array references (e.g. `y[idx_h2]`).

**Parameters**

**expr** : _sympy.Basic_
: Expression containing `nden` symbols.

**species_var** : _str, optional_
: Species array variable name. Default `"y"`.

**idx_prefix** : _str, optional_
: Prefix for species index names. Default `""`.

**brac_format** : _str, optional_
: Override bracket style. Default `""`.

**idx_offset** : _int, optional_
: Index offset. Default `-1`.

**Returns**

_str_
: Expression as a code string with species arrays substituted.
