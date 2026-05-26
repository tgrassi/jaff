---
tags:
    - Api
    - Code-generation
---

# get_ode_expressions_str

`#!python Codegen.get_ode_expressions_str(idx_offset=-1, flux_var="flux", species_var="y", idx_prefix="", derivative_prefix="d", derivative_var=None, brac_format="", assignment_op="", line_end="")`

Generates a code block for ODE right-hand sides expressed in terms of fluxes.

**Parameters**

**idx_offset** : _int, optional_
: Index offset. Default `-1`.

**flux_var** : _str, optional_
: Flux array name. Default `"flux"`.

**species_var** : _str, optional_
: Species array name. Default `"y"`.

**idx_prefix** : _str, optional_
: Prefix for species index names. Default `""`.

**derivative_prefix** : _str, optional_
: Prefix for derivative variable name. Default `"d"`.

**derivative_var** : _str or None, optional_
: Override full derivative array name. Default `None`.

**brac_format** : _str, optional_
: Override bracket format. Default `""`.

**assignment_op** : _str, optional_
: Override assignment operator. Default `""`.

**line_end** : _str, optional_
: Override statement terminator. Default `""`.

**Returns**

_str_
: ODE right-hand side code block.
