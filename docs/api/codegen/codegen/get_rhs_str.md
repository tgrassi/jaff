---
tags:
    - Api
    - Code-generation
---

# get_rhs_str

`#!python get_rhs_str(idx_offset=0, use_cse=True, cse_var="cse", ode_var="f", brac_format="", def_prefix="", assignment_op="", line_end="")`

Generates the complete RHS code block (ODE system + energy equation). The energy equation is assigned to `ode_var[n_species]`.

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
: Complete RHS code block including the energy equation.
