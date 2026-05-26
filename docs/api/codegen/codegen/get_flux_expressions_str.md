---
tags:
    - Api
    - Code-generation
---

# get_flux_expressions_str

`#!python get_flux_expressions_str(rate_var="k", species_var="y", idx_prefix="", idx_offset=-1, brac_format="", flux_var="flux", assignment_op="", line_end="")`

Generates a complete code block for all reaction fluxes.

**Parameters**

**rate_var** : _str, optional_
: Rate array name. Default `"k"`.

**species_var** : _str, optional_
: Species density array name. Default `"y"`.

**idx_prefix** : _str, optional_
: Prefix for species index names. Default `""`.

**idx_offset** : _int, optional_
: Index offset. Default `-1`.

**brac_format** : _str, optional_
: Override bracket format. Default `""`.

**flux_var** : _str, optional_
: Flux array name. Default `"flux"`.

**assignment_op** : _str, optional_
: Override assignment operator. Default `""`.

**line_end** : _str, optional_
: Override statement terminator. Default `""`.

**Returns**

_str_
: Flux code block.
