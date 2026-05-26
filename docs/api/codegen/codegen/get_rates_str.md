---
tags:
    - Api
    - Code-generation
---

# get_rates_str

`#!python get_rates_str(idx_offset=-1, rate_variable="k", brac_format="", use_cse=True, cse_var="x", var_prefix="", assignment_op="", line_end="")`

Generates a complete code block for all reaction rate coefficients.

**Parameters**

**idx_offset** : _int, optional_
: Starting index. Default `-1` (language default).

**rate_variable** : _str, optional_
: Rate array name. Default `"k"`.

**brac_format** : _str, optional_
: Override bracket format. Default `""`.

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"x"`.

**var_prefix** : _str, optional_
: Prefix for CSE variable declarations. Default `""`.

**assignment_op** : _str, optional_
: Override assignment operator. Default `""`.

**line_end** : _str, optional_
: Override statement terminator. Default `""`.

**Returns**

_str_
: Rate calculation code block.
