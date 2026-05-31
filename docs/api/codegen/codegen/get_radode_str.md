---
tags:
    - Api
    - Code-generation
---

# get_radode_str

`#!python get_radode_str(idx_offset=0, use_cse=True, cse_var="rcse", radode_var="f", brac_format="", def_prefix="", assignment_op="", line_end="", order=0)`

Generates a formatted code block for the radiation ODE system.

**Parameters**

**idx_offset** : _int, optional_
: Base index for the output array subscripts. Default `0`. Negative values use the language default (`0` for C/C++/Python/Rust, `1` for Fortran/Julia/R).

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"rcse"`.

**radode_var** : _str, optional_
: Name of the output radiation ODE array. Default `"f"`.

**brac_format** : _str, optional_
: Override 1-D bracket pair. Empty string uses the language default (`"[]"` for most languages, `"()"` for Fortran). Valid values: `"()"`, `"{}"`, `"[]"`, `"<>"`. Default `""`.

**def_prefix** : _str, optional_
: Type declaration prefix for CSE temporaries. Empty string uses the language default (`"const double "` for C/C++, `"const f64 "` for Rust, `"const Float64 "` for Julia, empty for Python/Fortran/R). Default `""`.

**assignment_op** : _str, optional_
: Assignment operator override. Empty string uses the language default (`"="` for most, `"<-"` for R). Default `""`.

**line_end** : _str, optional_
: Line terminator override. Empty string uses the language default (`";"` for C/C++/Rust, empty for Python/Fortran/Julia/R). Default `""`.

**order** : _int, optional_
: Radiation moment closure order passed to `get_indexed_radodes`. Valid values: `0`, `1`, `2`, `3` (see `get_indexed_radodes` for the layout convention). Default `0`.

**Returns**

_str_
: Radiation ODE system code block.

### Example

For a network with H photoionization (`H → H+ + e-`, 1 UV band \[13.6, ∞\] eV, photon-density mode), default settings (`order=0`) produce:

```python
f[0] = -4.72e-8*nden[H]*photden[0]
f[1] = -4.72e-8*nden[H]*rflux[0]
```

`f[0]` is the photon-density ODE (`d(photden[0])/dt`); `f[1]` is the flux ODE (`d(rflux[0])/dt`). CSE prefix defaults to `"rcse"` (not `"cse"`). With `order=1` the outputs are swapped: `f[0]` = flux, `f[1]` = density.

For C++ (`lang="cxx"`) with `def_prefix="const double "`:

```python
radodes = cg.get_radode_str(def_prefix="const double ")
```

**Output**

```cpp
const double rcse0 = 4.72e-8*nden[H];
f[0] = -rcse0*photden[0];
f[1] = -rcse0*rflux[0];
```
