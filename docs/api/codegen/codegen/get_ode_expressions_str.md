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
: Base index for flux array subscripts. Default `-1`, which uses the language default (`0` for C/C++/Python/Rust, `1` for Fortran/Julia/R).

**flux_var** : _str, optional_
: Flux array name. Default `"flux"`.

**species_var** : _str, optional_
: Species array name. Default `"y"`.

**idx_prefix** : _str, optional_
: Prefix prepended to each species index name, e.g. `"idx_"` yields `dy[idx_H]`. Default `""`.

**derivative_prefix** : _str, optional_
: Prefix prepended to `species_var` to form the derivative variable name when `derivative_var` is not given. Default `"d"` (yields `"dy"`).

**derivative_var** : _str or None, optional_
: Explicit name for the derivative array (overrides `derivative_prefix` + `species_var`). Default `None`.

**brac_format** : _str, optional_
: Override 1-D bracket pair. Empty string uses the language default (`"[]"` for most languages, `"()"` for Fortran). Valid values: `"()"`, `"{}"`, `"[]"`, `"<>"`. Default `""`.

**assignment_op** : _str, optional_
: Assignment operator override. Empty string uses the language default (`"="` for most, `"<-"` for R). Default `""`.

**line_end** : _str, optional_
: Line terminator override. Empty string uses the language default (`";"` for C/C++/Rust, empty for Python/Fortran/Julia/R). Default `""`.

**Returns**

_str_
: ODE right-hand side code block.

### Example

For a network with two species and two reactions, default settings produce:

```python
dy[H] = -flux[0] + flux[1]
dy[H2] = +flux[0] - flux[1]
```

For C++ (`lang="cxx"`) with `idx_prefix="idx_"`:

```python
ode = cg.get_ode_expressions_str(idx_prefix="idx_")
```

**Output**

```cpp
dy[idx_H] = -flux[0] + flux[1];
dy[idx_H2] = +flux[0] - flux[1];
```
