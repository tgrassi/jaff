---
tags:
    - Api
    - Code-generation
icon: lucide/braces
---

# Codegen

The `Codegen` class generates optimized code for chemical reaction networks in multiple programming languages.

## Overview

The `Codegen` class provides methods to generate code for:

- **Rate coefficient calculations** - Compute reaction rates
- **Flux expressions** - Calculate reaction fluxes
- **ODE systems** - Time derivatives of species concentrations
- **Jacobian matrices** - Partial derivatives for implicit solvers
- **Common constants** - Species indices and network metadata

Code generation uses SymPy for symbolic manipulation and applies optimizations like Common Subexpression Elimination (CSE) to improve performance.

```python
from jaff import Network, Codegen

# Load network
net = Network("networks/react_COthin")

# Create code generator
cg = Codegen(network=net, lang="c++")

# Generate code
rates = cg.get_rates_str(use_cse=True)
odes = cg.get_ode_str(use_cse=True)
jac = cg.get_jacobian_str(use_cse=True)
```

## Type Definitions

The `codegen` module uses TypedDict classes to provide structured, type-safe return values.

### ExtrasDict

```python
class ExtrasDict(TypedDict):
    """Container for extra data in IndexedReturn."""
    cse: IndexedList
```

Dictionary containing additional data alongside main expressions.

**Attributes**:

- `cse` (IndexedList): List of Common Subexpression Elimination (CSE) temporary variables
    - Contains `IndexedValue` objects representing CSE variable assignments
    - Example: `IndexedValue([0], "sqrt(tgas)")`

---

### IndexedReturn

```python
class IndexedReturn(TypedDict):
    """Structured return value for indexed code generation methods."""
    extras: ExtrasDict
    expressions: IndexedList
```

Return structure for methods that generate indexed expressions with optional CSE optimization.

**Attributes**:

- `extras` (ExtrasDict): Dictionary containing CSE temporaries and other auxiliary data
    - `extras["cse"]`: IndexedList of CSE temporary variable expressions
- `expressions` (IndexedList): List of main expressions
    - Contains `IndexedValue` objects for the primary output (rates, ODEs, Jacobian elements, etc.)

**Methods Returning IndexedReturn**:

- `get_indexed_rates()` - Rate coefficient expressions
- `get_indexed_odes()` - ODE right-hand side expressions
- `get_indexed_rhs()` - RHS expressions (alias for ODEs)
- `get_indexed_jacobian()` - Jacobian matrix elements

---

### LangModifier

```python
class LangModifier(TypedDict):
    """Language-specific code generation configuration."""
    brac: str
    assignment_op: str
    line_end: str
    matrix_sep: str
    code_gen: Callable[..., str]
    idx_offset: int
    comment: str
    types: dict[str, str]
    extras: dict[str, Any]
```

Type definition for language-specific code generation modifiers and settings.

**Attributes**:

- `brac` (str): Bracket style for 1D arrays
    - C/C++: `"[]"`
    - Fortran: `"()"`
- `assignment_op` (str): Assignment operator (typically `"="`)
- `line_end` (str): Statement terminator
    - C/C++: `";"`
    - Python/Fortran: `""`
- `matrix_sep` (str): Separator for 2D array indexing
    - C/C++: `"]["` (for `array[i][j]`)
    - Fortran: `", "` (for `array(i, j)`)
- `code_gen` (Callable): SymPy code generation function for the target language
- `idx_offset` (int): Array indexing offset
    - C/C++/Python: `0`
    - Fortran: `1`
- `comment` (str): Comment prefix
    - C/C++: `"//"`
    - Fortran: `"!!"`
    - Python: `"#"`
- `types` (dict\[str, str\]): Language-specific type declarations
    - Example: `{"double": "double", "int": "int"}` for C++
- `extras` (dict\[str, Any\]): Additional language-specific attributes
    - Qualifiers, specifiers, and other language features

**Usage**:

This structure is used internally by `Codegen` to maintain language-specific settings.

---

## Class Reference

<!-- ::: jaff.codegen.Codegen
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get_commons
        - get_rates_str
        - get_flux_expressions_str
        - get_ode_expressions_str
        - get_ode_str
        - get_jacobian_str
        - get_dedt
-->

```python
class Codegen:
    """
    Code generator for chemical reaction networks.

    Attributes:
        net (Network): Chemical reaction network
        lang (str): Target programming language
        code_gen: SymPy code generation function
        lb, rb (str): Array brackets
        mlb, mrb (str): Matrix brackets
        matrix_sep (str): Matrix index separator
        assignment_op (str): Assignment operator
        line_end (str): Statement terminator
    """
```

## Constructor

### `Codegen()`

Create a code generator for a specific language and network.

**Parameters:**

- `network` (Network): Chemical reaction network object
- `lang` (str): Target programming language. Default: "c++"
    - `"c++"`, `"cpp"`, `"cxx"` → C++
    - `"c"` → C
    - `"fortran"`, `"f90"` → Fortran 90
    - `"python"`, `"py"` → Python
    - `"rust"`, `"rs"` → Rust
    - `"julia"`, `"jl"` → Julia
    - `"r"` → R
- `brac_format` (str): Override 1D array bracket style. Default: "" (use language default)
    - Options: `"()"`, `"[]"`, `"{}"`, `"<>"`
- `matrix_format` (str): Override 2D array format. Default: "" (use language default)
    - Options: `"()"`, `"(,)"`, `"[]"`, `"[,]"`, `"{}"`, `"{,}"`, `"<>"`, `"<,>"`

**Returns:**

- `Codegen`: Initialized code generator

**Raises:**

- `ValueError`: If language, bracket format, or matrix format is not supported

**Example:**

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")

# C++ (default)
cg_cpp = Codegen(network=net, lang="c++")

# Fortran
cg_f90 = Codegen(network=net, lang="f90")

# Python with custom brackets
cg_py = Codegen(network=net, lang="python", brac_format="[]")

# C with 2D comma-separated indexing
cg_c = Codegen(network=net, lang="c", matrix_format="[,]")
```

## Attributes

| Attribute       | Type             | Description                                                                  |
| --------------- | ---------------- | ---------------------------------------------------------------------------- |
| `net`           | `Network`        | Chemical reaction network object                                             |
| `lang`          | `str`            | Internal language identifier ('cxx', 'c', 'f90', 'py', 'rust', 'julia', 'r') |
| `lb`            | `str`            | Left bracket for 1D arrays (e.g., '\[', '(')                                 |
| `rb`            | `str`            | Right bracket for 1D arrays (e.g., '\]', ')')                                |
| `mlb`           | `str`            | Left bracket for 2D arrays                                                   |
| `mrb`           | `str`            | Right bracket for 2D arrays                                                  |
| `matrix_sep`    | `str`            | Separator for 2D indices (e.g., '][', ', ')                                  |
| `assignment_op` | `str`            | Assignment operator (typically '=')                                          |
| `line_end`      | `str`            | Statement terminator (';' for C/C++, '' for Python/Fortran)                  |
| `code_gen`      | `Callable`       | SymPy code generation function                                               |
| `ioff`          | `int`            | Default array indexing offset (0 or 1)                                       |
| `comment`       | `str`            | Comment prefix ('//', '!!', '#')                                             |
| `types`         | `dict[str, str]` | Type declarations for the language                                           |
| `extras`        | `dict[str, Any]` | Additional language-specific attributes                                      |

## Methods

The `Codegen` class provides two types of methods:

1. **String Methods** - Return formatted code strings ready to use (e.g., `get_rates_str()`, `get_ode_str()`)
2. **Indexed Methods** - Return structured `IndexedReturn` dictionaries with `IndexedList` objects (e.g., `get_indexed_rates()`, `get_indexed_odes()`). This is primarily used by `FileParser` to produce templates.

### Common Constants

#### `get_commons()`

Generate code for common constants (species indices, counts).

**Parameters:**

- `idx_offset` (int): Starting index for species. Default: -1 (use language default)
- `idx_prefix` (str): Prefix for species index names (e.g., "idx\_"). Default: ""
- `definition_prefix` (str): Prefix for definitions (e.g., "const int "). Default: ""
- `assignment_op` (str): Override assignment operator. Default: "" (use language default)
- `line_end` (str): Override line terminator. Default: "" (use language default)

**Returns:**

- `str`: Generated code with species indices and counts

**Example:**

```python
# C++ style
commons = cg.get_commons(
    idx_offset=0,
    idx_prefix="idx_",
    definition_prefix="const int "
)
```

**Output (C++):**

```cpp
const int idx_h = 0;
const int idx_h2 = 1;
const int idx_o = 2;
const int nspecs = 35;
const int nreactions = 127;
```

### Rate Calculations

#### `get_indexed_rates()`

Generate indexed rate expressions with optional CSE optimization.

**Parameters:**

- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "x"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: `IndexedList` of CSE temporary expressions
    - `expressions`: `IndexedList` of rate expressions

**Example:**

```python
result = cg.get_indexed_rates(use_cse=True, cse_var="cse")

# Access CSE temporaries
for iv in result["extras"]["cse"]:
    print(f"const double cse[{iv.indices[0]}] = {iv.value};")

# Access rate expressions
for iv in result["expressions"]:
    print(f"k[{iv.indices[0]}] = {iv.value};")
```

**See Also**: [JAFF Types API](jaff-types.md) for details on `IndexedValue` and `IndexedList`.

---

#### `get_rates_str()`

Generate code for reaction rate coefficient calculations.

**Parameters:**

- `idx_offset` (int): Starting index for rate array. Default: -1 (use language default)
- `rate_variable` (str): Name of rate array variable. Default: "k"
- `brac_format` (str): Override bracket format. Default: ""
- `use_cse` (bool): Apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variables. Default: "x"
- `var_prefix` (str): Prefix for variable declarations. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated rate calculation code

**Example:**

```python
rates = cg.get_rates_str(
    idx_offset=0,
    rate_variable="k",
    use_cse=True
)
```

**Output (C++ with CSE):**

```cpp
//Common subexpressions
const double x0 = sqrt(tgas);
const double x1 = pow(tgas/300, 0.5);
const double x2 = exp(-500/tgas);

//Rate calculations using common subexpressions
k[0] = 1.2e-10 * x1;
k[1] = 3.4e-11 * x2;
k[2] = 5.6e-12 * x0 * x1;
```

### Flux Calculations

#### `get_indexed_flux_expressions()`

Generate indexed flux expressions for all reactions.

This method creates IndexedValue objects representing flux calculations for each reaction. Fluxes are the products of rate coefficients and reactant concentrations.

**Parameters:**

None

**Returns:**

- `IndexedList`: List of IndexedValue(\[reaction_idx\], flux_expression) objects
    - Each flux expression contains the template placeholder `$IDX$` for the reaction index
    - Uses language-specific bracket formats

**Note:**

- Flux expressions use template placeholders replaced during code generation
- Use `get_flux_expressions_str()` for formatted code strings
- Generated expressions are language-independent templates

**Example:**

```python
fluxes = cg.get_indexed_flux_expressions()
for iv in fluxes:
    print(f"Reaction {iv.indices[0]}: {iv.value}")
# Output:
# Reaction 0: k[$IDX$] * y[h] * y[o]
# Reaction 1: k[$IDX$] * y[co]
```

**See Also:**

- `get_flux_expressions_str()` - Generate formatted string output with variable names

---

#### `get_flux_expressions_str()`

Generate code for reaction flux calculations (rate × reactant concentrations).

Generate code for reaction flux calculations (rate × reactant concentrations).

**Parameters:**

- `rate_var` (str): Name of rate coefficient array. Default: "k"
- `species_var` (str): Name of species concentration array. Default: "y"
- `idx_prefix` (str): Prefix for species index names. Default: ""
- `idx_offset` (int): Starting index. Default: -1 (use language default)
- `brac_format` (str): Override bracket format. Default: ""
- `flux_var` (str): Name of flux array variable. Default: "flux"
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated flux calculation code

**Example:**

```python
fluxes = cg.get_flux_expressions_str(
    rate_var="k",
    species_var="n",
    idx_prefix="idx_",
    flux_var="flux"
)
```

**Output:**

```cpp
flux[0] = k[0] * n[idx_h] * n[idx_o];
flux[1] = k[1] * n[idx_h2] * n[idx_o];
flux[2] = k[2] * n[idx_c] * n[idx_o2];
```

### ODE Expressions

#### `get_indexed_ode_expressions()`

Generate indexed ODE expressions from flux contributions.

This method creates IndexedValue objects representing the time derivatives of species concentrations based on their participation in reactions (via fluxes).

**Parameters:**

None

**Returns:**

- `IndexedList`: List of IndexedValue(\[species_idx\], ode_expression) objects
    - Each ODE expression is the sum of flux contributions for that species
    - Uses language-specific bracket formats

**Note:**

- Does NOT apply CSE optimization (use `get_indexed_odes()` for CSE)
- Flux expressions must be generated separately
- Use `get_ode_expressions_str()` for formatted code strings

**Example:**

```python
ode_exprs = cg.get_indexed_ode_expressions()
for iv in ode_exprs:
    print(f"Species {iv.indices[0]}: dy/dt = {iv.value}")
```

**See Also:**

- `get_ode_expressions_str()` - Generate formatted string output
- `get_indexed_odes()` - Generate ODE system with CSE optimization

---

#### `get_indexed_odes()`

Generate indexed ODE expressions with optional CSE optimization.

**Parameters:**

- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: IndexedList of CSE temporary expressions
    - `expressions`: IndexedList of ODE right-hand side expressions

**Example:**

```python
result = cg.get_indexed_odes(use_cse=True)

# Generate CSE declarations
for iv in result["extras"]["cse"]:
    print(f"const double cse[{iv.indices[0]}] = {iv.value};")

# Generate ODE assignments
for iv in result["expressions"]:
    print(f"dydt[{iv.indices[0]}] = {iv.value};")
```

---

#### `get_ode_expressions_str()`

Generate code for ODE right-hand side (dy/dt) from fluxes.

**Parameters:**

- `idx_offset` (int): Starting index. Default: -1 (use language default)
- `flux_var` (str): Name of flux array. Default: "flux"
- `species_var` (str): Name of species array. Default: "y"
- `idx_prefix` (str): Prefix for species indices. Default: ""
- `derivative_prefix` (str): Prefix for derivative variable. Default: "d"
- `derivative_var` (str): Override derivative array name. Default: None
- `brac_format` (str): Override bracket format. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated ODE code

**Example:**

```python
odes = cg.get_ode_expressions_str(
    flux_var="flux",
    species_var="y",
    idx_prefix="idx_",
    derivative_prefix="d"
)
```

**Output:**

```cpp
dy[idx_h] = 0.0 - flux[0] + flux[1];
dy[idx_o] = 0.0 - flux[0] - flux[1] + flux[2];
dy[idx_oh] = 0.0 + flux[0] + flux[1];
```

### Optimized ODE System

#### `get_indexed_rhs()`

Generate indexed right-hand side expressions (ODE + energy equation).

This method combines the ODE system with the specific internal energy derivative (dedt). The energy equation is appended as the last element in the expressions list.

**Parameters:**

- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: IndexedList of CSE temporary expressions
    - `expressions`: IndexedList of RHS expressions (n_species + 1 elements, last is dedt)

**Note:**

- The energy equation is appended as the last element: `expressions[n_species]`
- CSE temporaries are shared from the ODE system
- Use `get_rhs_str()` for formatted code ready to write to file

**Example:**

```python
result = cg.get_indexed_rhs(use_cse=True)

# Last expression is the energy derivative
n_species = len(cg.net.species)
dedt_expr = result["expressions"][-1]
print(f"Energy equation at index {dedt_expr.indices[0]}: {dedt_expr.value}")
```

**See Also:**

- `get_rhs_str()` - Generate formatted string output
- `get_indexed_odes()` - Generate only ODE system without energy equation
- `get_dedt()` - Generate only the energy derivative expression

---

#### `get_rhs_str()`

Generate formatted code string for complete RHS (ODE + energy equation).

This method combines the ODE system with the specific internal energy derivative. The energy equation is appended as the last element in the output array.

**Parameters:**

- `idx_offset` (int): Starting index for arrays. Default: 0
- `use_cse` (bool): Apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"
- `ode_var` (str): Name of output array. Default: "f"
- `brac_format` (str): Override bracket format. Default: ""
- `def_prefix` (str): Prefix for variable declarations. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated code with ODE system followed by energy equation assignment

**Note:**

- Energy equation is assigned to `ode_var[n_species]`
- CSE optimizations from ODE system are included

**Example:**

```python
rhs = cg.get_rhs_str(
    idx_offset=0,
    use_cse=True,
    ode_var="f"
)
```

**Output:**

```cpp
const double cse0 = k[0] * n[0];
const double cse1 = k[1] * n[1];

f[0] = -cse0 + cse1;
f[1] = cse0 - cse1;
f[2] = (some energy equation expression);
```

---

#### `get_ode_str()`

Generate optimized ODE system with CSE applied to the entire system (without energy equation).

**Parameters:**

- `idx_offset` (int): Starting index. Default: 0
- `use_cse` (bool): Apply CSE optimization. Default: True
- `cse_var` (str): Prefix for CSE variables. Default: "cse"
- `ode_var` (str): Name of ODE output array. Default: "f"
- `brac_format` (str): Override bracket format. Default: ""
- `def_prefix` (str): Prefix for variable definitions. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated ODE code with CSE optimizations

**Note:** Results are cached after the first call.

**Example:**

```python
ode = cg.get_ode_str(
    idx_offset=0,
    use_cse=True,
    ode_var="dydt"
)
```

**Output:**

```cpp
const double cse0 = k[0] * n[0];
const double cse1 = k[1] * n[1];
const double cse2 = cse0 * n[2];

dydt[0] = -cse2 + cse1;
dydt[1] = -cse1 + cse0;
dydt[2] = cse2 - cse0;
```

### Jacobian Matrix

#### `get_indexed_jacobian()`

Generate indexed Jacobian matrix elements with optional CSE optimization.

**Parameters:**

- `use_dedt` (bool): Include energy equation derivatives. Default: False
- `use_cse` (bool): Whether to apply common subexpression elimination. Default: True
- `cse_var` (str): Prefix for CSE temporary variable names. Default: "cse"

**Returns:**

- `IndexedReturn`: Dictionary containing:
    - `extras["cse"]`: IndexedList of CSE temporary expressions
    - `expressions`: IndexedList of Jacobian elements with 2D indices

**Note**: Jacobian elements use 2D indexing (flattened representation).

**Example:**

```python
result = cg.get_indexed_jacobian(use_cse=True)

# CSE temporaries (1D indices)
for iv in result["extras"]["cse"]:
    print(f"const double cse[{iv.indices[0]}] = {iv.value};")

# Jacobian elements (2D indices)
for iv in result["expressions"]:
    i, j = iv.indices
    print(f"jac[{i}][{j}] = {iv.value};")

# Convert to nested representation
nested_jac = result["expressions"].nested()
for iv in nested_jac:
    row_idx = iv.indices[0]
    print(f"Row {row_idx}: {len(iv.value)} elements")
```

---

#### `get_jacobian_str()`

Generate analytical Jacobian matrix ($\partial f_i/\partial y_j$).

**Parameters:**

- `use_dedt` (bool): Include energy equation derivatives. Default: False
- `idx_offset` (int): Starting index. Default: 0
- `use_cse` (bool): Apply CSE optimization. Default: True
- `cse_var` (str): Prefix for CSE variables. Default: "cse"
- `jac_var` (str): Name of Jacobian matrix variable. Default: "J"
- `matrix_format` (str): Override 2D array format. Default: ""
- `var_prefix` (str): Prefix for CSE variable declarations. Default: ""
- `assignment_op` (str): Override assignment operator. Default: ""
- `line_end` (str): Override line terminator. Default: ""

**Returns:**

- `str`: Generated Jacobian code with CSE optimizations

**Note:** Results are cached after the first call.

**Example:**

```python
jac = cg.get_jacobian_str(
    idx_offset=0,
    use_cse=True,
    jac_var="J"
)
```

**Output:**

```cpp
const double cse0 = k[0] * n[1];
const double cse1 = k[1] * n[0];

J[0][0] = -cse1;
J[0][1] = -cse0;
J[1][0] = cse1;
J[1][1] = cse0;
```

### Energy Derivative

#### `get_dedt()`

Generate code for specific internal energy time derivative.

**Returns:**

- `str`: Generated code for d(e)/dt calculation

**Note:** Results are cached after the first call.

**Example:**

```python
dedt = cg.get_dedt()
```

## Language-Specific Defaults

### C/C++

```python
cg = Codegen(network=net, lang="c++")
```

- **Brackets**: `[]`
- **Matrix**: `[][]`
- **Index offset**: 0
- **Line end**: `;`
- **Comment**: `//`
- **Assignment**: `=`

### Fortran

```python
cg = Codegen(network=net, lang="f90")
```

- **Brackets**: `()`
- **Matrix**: `(,)`
- **Index offset**: 1
- **Line end**: ``
- **Comment**: `!!`
- **Assignment**: `=`

### Python

```python
cg = Codegen(network=net, lang="py")
```

- **Brackets**: `[]`
- **Matrix**: `[][]`
- **Index offset**: 0
- **Line end**: ``
- **Comment**: `#`
- **Assignment**: `=`

## Language-Specific Differences

### Indexing Conventions

Different languages use different array indexing conventions:

| Language | Index Offset | Default Bracket | Example    |
| -------- | ------------ | --------------- | ---------- |
| C        | 0-based      | `[]`            | `array[0]` |
| C++      | 0-based      | `[]`            | `array[0]` |
| Python   | 0-based      | `[]`            | `array[0]` |
| Rust     | 0-based      | `[]`            | `array[0]` |
| Fortran  | 1-based      | `()`            | `array(1)` |
| Julia    | 1-based      | `[]`            | `array[1]` |
| R        | 1-based      | `[]`            | `array[1]` |

### Statement Terminators

| Language | Terminator | Example  |
| -------- | ---------- | -------- |
| C        | `;`        | `x = 1;` |
| C++      | `;`        | `x = 1;` |
| Rust     | `;`        | `x = 1;` |
| Python   | (none)     | `x = 1`  |
| Fortran  | (none)     | `x = 1`  |
| Julia    | (none)     | `x = 1`  |
| R        | (none)     | `x <- 1` |

### Assignment Operators

| Language | Operator | Example  |
| -------- | -------- | -------- |
| C/C++    | `=`      | `x = 5;` |
| Python   | `=`      | `x = 5`  |
| Rust     | `=`      | `x = 5;` |
| Fortran  | `=`      | `x = 5`  |
| Julia    | `=`      | `x = 5`  |
| R        | `<-`     | `x <- 5` |

### Comment Styles

| Language | Prefix | Example                |
| -------- | ------ | ---------------------- |
| C/C++    | `//`   | `// This is a comment` |
| Rust     | `//`   | `// This is a comment` |
| Python   | `#`    | `# This is a comment`  |
| Julia    | `#`    | `# This is a comment`  |
| R        | `#`    | `# This is a comment`  |
| Fortran  | `!!`   | `!! This is a comment` |

### Type Declarations

**C/C++:**

```cpp
const double x = 1.0;
const int i = 42;
const bool flag = true;
```

**Rust:**

```rust
const x: f64 = 1.0;
const i: i32 = 42;
const flag: bool = true;
```

**Julia:**

```julia
const x::Float64 = 1.0
const i::Int64 = 42
const flag::Bool = true
```

**Python, R, Fortran:**
No explicit type declarations in generated code.

## See Also

- [JAFF Types API](jaff-types.md) - IndexedValue and IndexedList type definitions
- [Network API](network.md) - Loading and analyzing networks
- [File Parser API](file-parser.md) - Template-based code generation
- [User Guide: Code Generation](../user-guide/code-generation.md) - Detailed guide

---

**Next**: Learn about [Template-Based Generation](file-parser.md) with the Fileparser class.
