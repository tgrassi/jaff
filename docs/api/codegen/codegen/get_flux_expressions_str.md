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
: Prefix prepended to species index names inside the expression, e.g. `"idx_"` yields `y[idx_H]`. Default `""`.

**idx_offset** : _int, optional_
: Base index for array subscripts. Default `-1`, which uses the language default (`0` for C/C++/Python/Rust, `1` for Fortran/Julia/R).

**brac_format** : _str, optional_
: Override 1-D bracket pair. Empty string uses the language default (`"[]"` for most languages, `"()"` for Fortran). Valid values: `"()"`, `"{}"`, `"[]"`, `"<>"`. Default `""`.

**flux_var** : _str, optional_
: Flux array name. Default `"flux"`.

**assignment_op** : _str, optional_
: Assignment operator override. Empty string uses the language default (`"="` for most, `"<-"` for R). Default `""`.

**line_end** : _str, optional_
: Line terminator override. Empty string uses the language default (`";"` for C/C++/Rust, empty for Python/Fortran/Julia/R). Default `""`.

**Returns**

_str_
: Flux code block.

### Example

For a network with two reactions, default settings produce:

```python
flux[0] = k[0] * y[H] * y[H2]
flux[1] = k[1] * y[H2]
```

For C++ (`lang="cxx"`) with `idx_prefix="idx_"`:

```python
fluxes = cg.get_flux_expressions_str(idx_prefix="idx_")
```

**Output**

```cpp
flux[0] = k[0] * y[idx_H] * y[idx_H2];
flux[1] = k[1] * y[idx_H2];
```
