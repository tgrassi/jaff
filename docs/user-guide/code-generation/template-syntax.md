---
tags:
    - User-guide
    - Code-generation
    - Template
icon: lucide/form
---

# Template Syntax

JAFF templates are ordinary source files (C, C++, Fortran, Python, Rust, Julia, R — or any custom format) that contain special `$JAFF` directives. The `TemplateParser` reads each file line-by-line, expands all directives against the loaded network, and writes the result to the output directory.

Templates can be processed from the CLI ([jaffgen](jaffgen.md)) or directly in Python:

```python
from jaff import Network
from jaff.codegen import TemplateParser
from pathlib import Path

net = Network("networks/react_COthin")
parser = TemplateParser(net, Path("rates.cpp"))
output = parser.parse_file()
```

---

## Directive Syntax

Every JAFF directive appears on a line that starts with a language comment followed by `$JAFF`:

```text
// $JAFF COMMAND arguments
content to expand
// $JAFF END
```

The comment token is detected automatically from the file extension (`//` for C/C++/Rust, `#` for Python/R, `!` for Fortran, `--` for SQL/Lua, etc.). Substitution tokens in the content are written as `$token_name$`.

---

## Commands

| Command  | Purpose |
| -------- | ------- |
| `SUB`    | Substitute scalar network values (species count, label, etc.) |
| `REPEAT` | Iterate over collections or generate indexed expressions |
| `GET`    | Retrieve a specific property for a named entity |
| `HAS`    | Check whether a species, reaction, or element exists |
| `REDUCE` | Generate sum expressions over a collection |
| `END`    | Close a directive block |

All commands accept an optional `$[REPLACE pattern replacement ...]$` modifier list (see [REPLACE Directive](#replace-directive)).

---

## SUB

Substitutes one or more scalar network values into the template content.

**Syntax:**
```text
// $JAFF SUB var1, var2, ...
content with $var1$, $var2$ tokens
// $JAFF END
```

**Available tokens:**

| Token      | Type   | Description |
| ---------- | ------ | ----------- |
| `nspec`    | `int`  | Number of species |
| `nreact`   | `int`  | Number of reactions |
| `nelem`    | `int`  | Number of elements |
| `nbands`   | `int`  | Number of radiation bands (0 if none) |
| `label`    | `str`  | Network label |
| `filename` | `str`  | Template file name |
| `filepath` | `Path` | Full template file path |
| `e_idx`    | `int`  | Index of the electron species |
| `dedt`     | `str`  | Language-specific internal energy equation |

Integer tokens support inline arithmetic with `+`, `-`, `*`, `/`:

```cpp
// $JAFF SUB nspec
#define NSPEC    $nspec$
#define NSPEC_P1 $nspec+1$
// $JAFF END
```

**Example output** (35 species):
```cpp
#define NSPEC    35
#define NSPEC_P1 36
```

---

## REPEAT

Iterates over a network collection and generates one block per item (vertical mode) or an inline array (horizontal mode).

**Syntax (vertical — `idx` present in variable list):**
```text
// $JAFF REPEAT idx, var IN collection $[modifiers]$
content[$idx$] = $var$;
// $JAFF END
```

**Syntax (horizontal — no `idx`):**
```text
// $JAFF REPEAT var IN collection
double arr[] = {$var$, };
// $JAFF END
```

### Vertical mode

One output line per collection item. Use `$idx$` for the zero-based index and `$idx+N$` / `$idx-N$` for offset indices. The number of `$idx` tokens in a line must match the dimensionality of the collection (1D vs 2D for matrices).

```cpp
// $JAFF REPEAT idx, specie IN species
species_names[$idx$] = "$specie$";
// $JAFF END
```

Output:
```cpp
species_names[0] = "H";
species_names[1] = "H+";
species_names[2] = "E";
```

### Horizontal mode

Expands into a bracket-enclosed list. The template must contain the variable inside brackets with optional quotes and a separator.

```cpp
// $JAFF REPEAT specie_charge IN specie_charges
double charges[] = {$specie_charge$, };
// $JAFF END
```

Output:
```cpp
double charges[] = {0, 1, -1};
```

### CSE (Common Subexpression Elimination)

`rates`, `odes`, `rhses`, and `jacobian` support a third variable `cse` that extracts repeated sub-expressions into named temporaries.

```cpp
// $JAFF REPEAT idx, rate, cse IN rates
const double x$idx$ = $cse$;
k[$idx$] = $rate$;
// $JAFF END
```

### Modifiers

Modifiers go inside `$[...]$` at the end of the command line.

| Modifier   | Values       | Description | Supported |
| ---------- | ------------ | ----------- | --------- |
| `SORT`     | `TRUE/FALSE` | Sort items before expansion | All |
| `USE_DEDT` | `TRUE/FALSE` | Include internal-energy equation in Jacobian | `jacobian` |
| `RADIATION`| `TRUE/FALSE` | Include radiation ODEs | `rhses` |
| `REPLACE`  | `pat repl`   | Regex replacement on output | All |

### Expression-generating collections

| Collection         | Variables              | Description | CSE |
| ------------------ | ---------------------- | ----------- | --- |
| `rates`            | `idx, rate`            | Rate coefficient expressions | ✓ |
| `odes`             | `idx, ode`             | Full ODE expressions (dydt) | ✓ |
| `rhses`            | `idx, rhs`             | RHS including dE/dt | ✓ |
| `flux_expressions` | `idx, flux_expression` | Flux = rate × reactant densities | ✗ |
| `ode_expressions`  | `idx, ode_expression`  | ODE terms without assignment | ✗ |
| `jacobian`         | `idx, expr`            | Jacobian matrix elements (2D) | ✓ |
| `radodes`          | `idx, radode`          | Radiation moment ODEs | ✗ |

### List-iterating collections

**Species:**

| Collection                   | Variable                    |
| ---------------------------- | --------------------------- |
| `species`                    | `specie`                    |
| `species_with_normalized_sign` | `specie_with_normalized_sign` |
| `specie_masses`              | `specie_mass`               |
| `specie_charges`             | `specie_charge`             |
| `specie_masses_ne`           | `specie_mass_ne`            |
| `specie_charges_ne`          | `specie_charge_ne`          |
| `neutral_species`            | `neutral_specie`            |
| `charged_species`            | `charged_specie`            |
| `neutral_specie_indices`     | `neutral_specie_index`      |
| `charged_specie_indices`     | `charged_specie_index`      |
| `charged_specie_indices_ne`  | `charged_specie_index_ne`   |
| `neutral_specie_masses`      | `neutral_specie_mass`       |
| `charged_specie_masses`      | `charged_specie_mass`       |
| `charged_specie_masses_ne`   | `charged_specie_mass_ne`    |
| `charge_truths`              | `charge_truth`              |
| `charge_truths_ne`           | `charge_truth_ne`           |

**Reactions:**

| Collection               | Variable               |
| ------------------------ | ---------------------- |
| `reactions`              | `reaction`             |
| `reactants`              | `reactant`             |
| `products`               | `product`              |
| `photo_reactions`        | `photo_reaction`       |
| `photo_reaction_indices` | `photo_reaction_index` |
| `photo_reaction_truths`  | `photo_reaction_truth` |
| `tmins`                  | `tmin`                 |
| `tmaxes`                 | `tmax`                 |

**Elements:**

| Collection               | Variable  |
| ------------------------ | --------- |
| `elements`               | `element` |
| `element_density_matrix` | `element` |
| `element_truth_matrix`   | `element` |

---

## GET

Retrieves a specific property for a named entity (species, reaction, or element).

**Syntax:**
```text
// $JAFF GET property FOR entity_name
content with $property$ token
// $JAFF END
```

**Available properties:**

| Property            | Entity type | Returns |
| ------------------- | ----------- | ------- |
| `specie_idx`        | species name | `int` — index in species array |
| `specie_mass`       | species name | `float` — mass in amu |
| `specie_charge`     | species name | `int` — charge |
| `specie_latex`      | species name | `str` — LaTeX name |
| `element_idx`       | element symbol | `int` — index in element array |
| `reaction_idx`      | verbatim reaction | `int` — index in reaction array |
| `reaction_tmin`     | verbatim reaction | `float` — minimum temperature |
| `reaction_tmax`     | verbatim reaction | `float` — maximum temperature |
| `reaction_verbatim` | verbatim reaction | `str` — verbatim string |

```cpp
// $JAFF GET specie_idx FOR H+
const int hplus_idx = $specie_idx$;
// $JAFF END

// $JAFF GET specie_mass FOR CO
const double co_mass = $specie_mass$;  // amu
// $JAFF END
```

---

## HAS

Returns `1` if an entity exists in the network, `0` otherwise.

**Syntax:**
```text
// $JAFF HAS identity entity_name
content with $identity$ token (expands to 0 or 1)
// $JAFF END
```

**Available identities:** `specie`, `reaction`, `element`

```cpp
// $JAFF HAS specie E
const int HAS_ELECTRON = $specie$;
// $JAFF END

// $JAFF HAS element C
const int HAS_CARBON = $element$;
// $JAFF END
```

---

## REDUCE

Generates a sum expression over a collection, expanding `$( expression )$` by iterating over each item.

**Syntax:**
```text
// $JAFF REDUCE var1, var2 IN collection1, collection2
result = $($var1$ * arr[$var2$])$;
// $JAFF END
```

The expression inside `$()$` is repeated and joined with ` + `. Multiple collections must have the same length.

```cpp
// Sum of all species charges
// $JAFF REDUCE specie_charge IN specie_charges
double total_charge = $($specie_charge$)$;
// $JAFF END
// Output: double total_charge = 0 + 1 + -1 + 0;

// Electron density from charge balance
// $JAFF REDUCE charged_specie_index_ne, charged_specie_charge_ne IN charged_specie_indices_ne, charged_specie_charges_ne
ne = $($charged_specie_charge_ne$ * xn[$charged_specie_index_ne$])$;
// $JAFF END
```

---

## REPLACE Directive

All commands accept a `REPLACE` modifier inside `$[...]$` that applies Python regex substitution to the generated output **after** expansion.

Multiple `REPLACE` pairs can be chained and are applied in sequence.

```text
// $JAFF REPEAT idx, specie IN species $[REPLACE \+ _plus REPLACE - _minus]
const int idx_$specie$ = $idx$;
// $JAFF END
```

Output:
```cpp
const int idx_H_plus = 0;
const int idx_e_minus = 1;
```

Capture groups are supported:
```text
// $JAFF REPEAT idx, specie IN species $[REPLACE (H)(\d+) \1_\2]
arr[$idx$] = "$specie$";
// $JAFF END
```
