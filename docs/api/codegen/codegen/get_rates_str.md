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
: Base index for array subscripts. Default `-1`, which uses the language default (`0` for C/C++/Python/Rust, `1` for Fortran/Julia/R).

**rate_variable** : _str, optional_
: Rate array name. Default `"k"`.

**brac_format** : _str, optional_
: Override 1-D bracket pair. Empty string uses the language default (`"[]"` for most languages, `"()"` for Fortran). Valid values: `"()"`, `"{}"`, `"[]"`, `"<>"`. Default `""`.

**use_cse** : _bool, optional_
: Apply common subexpression elimination. Default `True`.

**cse_var** : _str, optional_
: CSE variable prefix. Default `"x"`.

**var_prefix** : _str, optional_
: Type declaration prefix for CSE temporaries. Empty string uses the language default (`"const double "` for C/C++, `"const f64 "` for Rust, `"const Float64 "` for Julia, empty for Python/Fortran/R). Default `""`.

**assignment_op** : _str, optional_
: Assignment operator override. Empty string uses the language default (`"="` for most, `"<-"` for R). Default `""`.

**line_end** : _str, optional_
: Line terminator override. Empty string uses the language default (`";"` for C/C++/Rust, empty for Python/Fortran/Julia/R). Default `""`.

**Returns**

_str_
: Rate calculation code block. Each line is separated by a new line character.

### Example

For a network with two reactions, default settings produce:

```python
k[0] = 1.5e-10*tgas**(-0.5)
k[1] = 3.2e-9
```

For C++ (`lang="cxx"`) with `var_prefix="const double "`:

```python
rates = cg.get_rates_str(var_prefix="const double ")
```

**Output**

```cpp
const double x0 = pow(tgas, -0.5);
k[0] = 1.5e-10*x0;
k[1] = 3.2e-9;
```

where `x0` is the generated cse
