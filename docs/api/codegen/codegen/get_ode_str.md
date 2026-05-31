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
: Base index for species ODE array subscripts. Default `0`. Negative values use the language default (`0` for C/C++/Python/Rust, `1` for Fortran/Julia/R).

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"cse"`.

**ode_var** : _str, optional_
: Output array name. Default `"f"`.

**brac_format** : _str, optional_
: Override 1-D bracket pair. Empty string uses the language default (`"[]"` for most languages, `"()"` for Fortran). Valid values: `"()"`, `"{}"`, `"[]"`, `"<>"`. Default `""`.

**def_prefix** : _str, optional_
: Type declaration prefix for CSE temporaries. Empty string uses the language default (`"const double "` for C/C++, `"const f64 "` for Rust, `"const Float64 "` for Julia, empty for Python/Fortran/R). Default `""`.

**assignment_op** : _str, optional_
: Assignment operator override. Empty string uses the language default (`"="` for most, `"<-"` for R). Default `""`.

**line_end** : _str, optional_
: Line terminator override. Empty string uses the language default (`";"` for C/C++/Rust, empty for Python/Fortran/Julia/R). Default `""`.

**Returns**

_str_
: ODE system code block.

### Example

For a network with two species and two reactions, default settings produce:

```python
f[0] = -1.5e-10*tgas**(-0.5)*y[H]*y[H2]
f[1] = 1.5e-10*tgas**(-0.5)*y[H]*y[H2]
```

For C++ (`lang="cxx"`) with `def_prefix="const double "`:

```python
ode = cg.get_ode_str(def_prefix="const double ")
```

**Output**

```cpp
const double cse0 = pow(tgas, -0.5);
f[0] = -1.5e-10*cse0*y[H]*y[H2];
f[1] = 1.5e-10*cse0*y[H]*y[H2];
```
