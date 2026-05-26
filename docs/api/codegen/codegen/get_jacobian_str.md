---
tags:
    - Api
    - Code-generation
---

# get_jacobian_str

`#!python get_jacobian_str(use_dedt=False, idx_offset=0, use_cse=True, cse_var="cse", jac_var="J", matrix_format="", var_prefix="", assignment_op="", line_end="")`

Generates the complete Jacobian matrix code block. Result is cached after the first call.

**Parameters**

**use_dedt** : _bool, optional_
: Include energy equation derivatives. Default `False`.

**idx_offset** : _int, optional_
: Starting index. Default `0`.

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**jac_var** : _str, optional_
: Jacobian array name. Default `"J"`.

**matrix_format** : _str, optional_
: Override 2D format. Default `""`.

**var_prefix** : _str, optional_
: Prefix for CSE variable declarations. Default `""`.

**assignment_op** : _str, optional_
: Override assignment operator. Default `""`.

**line_end** : _str, optional_
: Override statement terminator. Default `""`.

**Returns**

_str_
: Jacobian code block.
