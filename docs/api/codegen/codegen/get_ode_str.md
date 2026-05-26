---
tags:
    - Api
    - Code-generation
---

# get_ode_str

`#!python get_ode_str(idx_offset=0, use_cse=True, cse_var="cse", ode_var="f", brac_format="", def_prefix="", assignment_op="", line_end="")`

Generates the complete ODE system (without energy equation) as a formatted code block. Result is cached after the first call.

**Parameters**

**idx_offset** : _int, optional_
: Starting index. Default `0`.

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**ode_var** : _str, optional_
: Output array name. Default `"f"`.

**brac_format** : _str, optional_
: Override bracket format. Default `""`.

**def_prefix** : _str, optional_
: Prefix for CSE variable declarations. Default `""`.

**assignment_op** : _str, optional_
: Override assignment operator. Default `""`.

**line_end** : _str, optional_
: Override statement terminator. Default `""`.

**Returns**

_str_
: ODE system code block.
