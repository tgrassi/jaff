---
tags:
    - User-guide
    - Code-generation
icon: lucide/settings
---

# Codegen

`Codegen` is the low-level code-generation engine at the core of JAFF. Given a parsed `Network` and a target language, it produces formatted assignment strings for reaction rates, fluxes, ODE right-hand sides, Jacobians, and radiation ODEs. All output strings are ready to paste into source files.

```python
from jaff import Network
from jaff.codegen import Codegen

net = Network("networks/GOW/GOW.jet")
cg = Codegen(net, lang="python")

print(cg.get_rates_str())
print(cg.get_ode_str())
```

---

## Constructor

```python
Codegen(network, lang="c++", brac_format="", matrix_format="")
```

| Parameter       | Type     | Default  | Description |
| --------------- | -------- | -------- | ----------- |
| `network`       | `Network`| —        | Parsed chemical reaction network |
| `lang`          | `str`    | `"c++"` | Target language (see [Supported Languages](#supported-languages)) |
| `brac_format`   | `str`    | `""`     | Override 1-D array brackets: `"[]"`, `"()"`, `"{}"`, `"<>"` |
| `matrix_format` | `str`    | `""`     | Override 2-D bracket/separator: `"[]"`, `"[,]"`, `"()"`, `"(,)"`, `"[][}"`, etc. |

**Raises** `ValueError` if `lang`, `brac_format`, or `matrix_format` is not supported.

---

## Supported Languages

| Alias(es)              | Canonical | Brackets | Index base | Comment |
| ---------------------- | --------- | -------- | ---------- | ------- |
| `c++`, `cpp`, `cxx`   | `cxx`     | `[]`     | 0          | `//`    |
| `c`                    | `c`       | `[]`     | 0          | `//`    |
| `fortran`, `f90`       | `fortran` | `()`     | 1          | `!`     |
| `python`, `py`         | `python`  | `[]`     | 0          | `#`     |
| `rust`, `rs`           | `rust`    | `[]`     | 0          | `//`    |
| `julia`, `jl`          | `julia`   | `[]`     | 1          | `#`     |
| `r`                    | `r`       | `[]`     | 1          | `#`     |

---

## Methods

### `#!python get_commons()`

Generates species index definitions and network-size constants.

```python
cg.get_commons(
    idx_offset=-1,       # -1 = use language default
    idx_prefix="",       # prepend to species index name, e.g. "idx_"
    definition_prefix="",# prepend to each line, e.g. "const int "
    assignment_op="",    # empty = language default
    line_end="",         # empty = language default
)
```

**Example output** (C++, 2 species):

```cpp
const int idx_H  = 0;
const int idx_H2 = 1;
const int nspecs = 2;
const int nreactions = 5;
```

---

### `#!python get_rates_str()`

Generates rate-coefficient assignment code for all reactions, with optional CSE.

```python
cg.get_rates_str(
    idx_offset=-1,       # -1 = language default
    rate_variable="k",   # name of the rate array
    brac_format="",      # override 1-D brackets
    use_cse=True,        # enable common subexpression elimination
    cse_var="x",         # prefix for CSE temporaries: x0, x1, ...
    var_prefix="",       # type prefix for CSE temporaries
    assignment_op="",    # override assignment operator
    line_end="",         # override line terminator
)
```

**Example output** (C++):

```cpp
const double x0 = exp(-1.0/tgas);
k[0] = 1.8e-11 * x0;
k[1] = photorates(1, G0, av, chi);
k[2] = 3.2e-17;
```

`photorates($IDX$, ...)` placeholders are automatically replaced with concrete reaction indices.

---

### `#!python get_flux_expressions_str()`

Generates flux assignment code: `flux[i] = k[i] * y[r1] * y[r2]`.

```python
cg.get_flux_expressions_str(
    rate_var="k",        # rate array name
    species_var="y",     # density array name
    idx_prefix="",       # species index prefix, e.g. "idx_"
    idx_offset=-1,
    brac_format="",
    flux_var="flux",     # flux array name
    assignment_op="",
    line_end="",
)
```

**Example output** (Python):

```python
flux[0] = k[0] * y[idx_H] * y[idx_H2]
flux[1] = k[1] * y[idx_H]
```

---

### `#!python get_ode_expressions_str()`

Generates ODE flux-sum expressions referencing a pre-computed `flux` array.

```python
cg.get_ode_expressions_str(
    idx_offset=-1,
    brac_format="",
    ode_var="f",
    flux_var="flux",
    assignment_op="",
    line_end="",
)
```

**Example output** (Python):

```python
f[0] = -flux[0] + flux[2]
f[1] =  flux[0] - flux[1]
```

---

### `#!python get_ode_str()`

Generates full ODE RHS code with rate expressions inlined and CSE applied across all species simultaneously.

```python
cg.get_ode_str(
    idx_offset=0,
    use_cse=True,
    cse_var="cse",       # prefix for CSE temporaries
    ode_var="f",
    brac_format="",
    def_prefix="",       # type declaration prefix for CSE temporaries
    assignment_op="",
    line_end="",
)
```

**Example output** (C++):

```cpp
const double cse0 = exp(-1.0/tgas);
const double cse1 = 1.8e-11 * cse0;
f[0] = -cse1 * y[0] * y[1] + 3.2e-17 * y[2];
f[1] =  cse1 * y[0] * y[1] - 2.7e-10 * y[1];
```

---

### `#!python get_rhs_str()`

Generates the combined RHS: species ODEs + energy derivative + (optional) radiation ODEs. CSE is applied jointly across all equations for maximum sub-expression sharing.

```python
cg.get_rhs_str(
    idx_offset=0,
    use_cse=True,
    cse_var="cse",
    ode_var="f",
    brac_format="",
    def_prefix="",
    assignment_op="",
    line_end="",
    specific_eint=False, # normalise energy deriv by density
    norm=0,              # 0 = mass density, 1 = number density
    radiation=False,     # include radiation ODEs
    rad_order=0,         # radiation moment closure order
)
```

Output order:

1. CSE temporaries
2. `f[0]` … `f[N-1]` — species density ODEs
3. `f[N]` — energy time-derivative `dE/dt`
4. `f[N+1]` … — radiation ODEs (only when `radiation=True`)

---

### `#!python get_dedt()`

Returns a single expression string for the energy time-derivative.

```python
cg.get_dedt(
    specific_eint=False, # normalise by density
    norm=0,              # 0 = mass density, 1 = number density
)
```

**Returns** `str` — one expression, no assignment or line terminator.

---

### `#!python get_radode_str()`

Generates radiation moment ODE assignment code.

```python
cg.get_radode_str(
    order=0,             # radiation moment closure order (0-3)
    idx_offset=0,
    use_cse=True,
    cse_var="rcse",
    radode_var="f",
    brac_format="",
    def_prefix="",
    assignment_op="",
    line_end="",
)
```

---

### `#!python get_jacobian_str()`

Generates the analytical Jacobian `J[i][j] = ∂f_i/∂y_j` for non-zero elements only (sparse).

```python
cg.get_jacobian_str(
    use_dedt=False,      # include energy equation row/column
    idx_offset=0,
    use_cse=True,
    cse_var="cse",
    jac_var="J",
    matrix_format="",    # override 2-D bracket style
    var_prefix="",
    assignment_op="",
    line_end="",
)
```

**Example output** (C++):

```cpp
const double cse0 = exp(-1.0/tgas);
J[0][0] = -1.8e-11 * cse0 * y[1];
J[0][1] = -1.8e-11 * cse0 * y[0];
J[1][1] = -2.7e-10;
```

Only non-zero Jacobian elements are emitted. User-defined functions (e.g. `#!python photorates(...)`) that cannot be symbolically differentiated are replaced with named partial-function calls: `#!python photorates_partial_0(...)`.

---

### `#!python get_language_tokens()`

Static method returning the `LangModifier` configuration for all supported languages.

```python
tokens = Codegen.get_language_tokens()
print(tokens["python"]["comment"])  # "#"
print(tokens["fortran"]["idx_offset"])  # 1
```

Each `LangModifier` contains: `brac`, `assignment_op`, `line_end`, `matrix_sep`, `code_gen`, `idx_offset`, `comment`, `types`, `extras`.

---

## Common Subexpression Elimination (CSE)

Most `get_*_str()` methods accept `use_cse=True` (the default). When enabled, SymPy's `#!python sympy.cse()` extracts repeated sub-expressions into named temporaries before the main assignments, reducing redundant computation in the generated code.

```python
# CSE disabled — every rate expression is fully expanded inline
cg.get_rates_str(use_cse=False)

# CSE enabled (default) — shared sub-expressions factored out
cg.get_rates_str(use_cse=True, cse_var="tmp")
```

Photorates calls and raw-string rates are excluded from CSE because they cannot be symbolically simplified.

---

## Full Example

```python
from jaff import Network
from jaff.codegen import Codegen

net = Network("networks/GOW/GOW.jet")
cg = Codegen(net, lang="c++")

# Write a minimal C++ ODE solver file
with open("output/network.cpp", "w") as f:
    f.write("#include <cmath>\n\n")
    f.write("// Species indices\n")
    f.write(cg.get_commons(definition_prefix="const int "))
    f.write("\nvoid rates(double* k, double tgas) {\n")
    f.write(cg.get_rates_str())
    f.write("}\n\n")
    f.write("void rhs(double* f, double* y, double tgas) {\n")
    f.write(cg.get_rhs_str())
    f.write("}\n")
```
