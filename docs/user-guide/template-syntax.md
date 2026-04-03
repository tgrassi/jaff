---
tags:
    - User-guide
    - Code-generation
    - Template
icon: lucide/form
---

# Template Syntax

## Introduction

JAFF templates enable code generation for chemical reaction networks across multiple programming languages (C, C++, Fortran, Python, Rust, Julia, R or any custom language). Templates are text files containing special JAFF directives that are processed by the `Fileparser` class to generate network-specific code.

Templates can be processed either programmatically or via the command-line interface:

### Using the Command Line

```bash
# Process templates using jaffgen
jaffgen --network networks/react_COthin --indir templates/ --outdir output/

# Use predefined template collections
jaffgen --network networks/react_COthin --template chemistry_solver --outdir output/

# Process specific files with language hint
jaffgen --network networks/test.dat --files rates.txt odes.txt --lang rust --outdir output/
```

For detailed information about command-line usage, see the [jaffgen Command Reference](jaffgen-command.md).

### Using the Python API

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# Load network
net = Network("networks/react_COthin")

# Process template
parser = Fileparser(net, Path("template.cpp"))
output = parser.parse_file()

# Save result
with open("output.cpp", "w") as f:
    f.write(output)
```

## Command Syntax

All JAFF commands follow this format:

```
// $JAFF COMMAND arguments
content to be generated
// $JAFF END
```

where // represents a comment in the designated laguage

Commands are enclosed in `// $JAFF` markers and terminated with `// $JAFF END`. The content between the command and END is processed according to the command type.

All substitutables are enclosed within `$$`

```cpp
// $JAFF SUB var1, var2
const int x = $var1$;
const int y = $var2$;
```

## Available Commands

| Command  | Purpose                                          | Typical Use Case                                      |
| -------- | ------------------------------------------------ | ----------------------------------------------------- |
| `SUB`    | Substitute network metadata values               | Insert constants like species count, network label    |
| `REPEAT` | Iterate over collections or generate expressions | Loop over species, reactions, generate rate equations |
| `GET`    | Access specific properties by name               | Retrieve mass of a particular species                 |
| `HAS`    | Conditional code inclusion                       | Include code only if a species/reaction exists        |
| `REDUCE` | Generate reduction/summation expressions         | Calculate total mass, sum of charges                  |
| `END`    | Terminate command blocks                         | Close SUB, REPEAT, HAS, or REDUCE blocks              |

## Quick Start Examples

### Example 1: Basic Substitution

```cpp
// Template
// $JAFF SUB nspec, nreact
const int NUM_SPECIES = $nspec$;
const int NUM_REACTIONS = $nreact$;
// $JAFF END

// Output (for a network with 35 species, 127 reactions)
const int NUM_SPECIES = 35;
const int NUM_REACTIONS = 127;
```

### Example 2: Simple Iteration

```cpp
// Template
// $JAFF REPEAT idx, specie IN species
species_names[$idx$] = "$specie$";
// $JAFF END

// Output
species_names[0] = "H";
species_names[1] = "H2";
species_names[2] = "O";
// ... etc
```

### Example 3: Generate Rate Equations

```cpp
// Template
void compute_rates(double* k, double tgas) {
// $JAFF REPEAT idx, rate, cse IN rates
    const double x$idx$ = $cse$;
    k[$idx$] = $rate$;  // $reaction$
// $JAFF END
}

// Output
void compute_rates(double* k, double tgas) {
    // Common subexpressions
    const double x0 = sqrt(tgas);
    const double x1 = pow(tgas/300.0, 0.5);

    k[0] = 1.2e-10 * x1;  // H + H -> H2
    k[1] = 3.4e-11 * x0 * exp(-500.0/tgas);  // H2 + O -> H + OH
    k[2] = 5.6e-12 * x0 * x1;  // OH + H2 -> H2O + H
    // ... etc
}
```

### Example 4: Conditional Inclusion

```cpp
// Template
// $JAFF HAS specie e-
const has_e = $specie$;
// $JAFF END
if (has_e) {
// Electron chemistry is included
// $JAFF GET specie_idx FOR e-
    const int electron_idx = $specie_idx$;
// $JAFF END
}

// Output (if e- exists in network)
// Electron chemistry is included
const has_e = 1;
if has_e {
    const int electron_idx = 12;
}
```

## Command Reference

## SUB Command

**Purpose:** Substitute multiple values from the network metadata.

**Syntax:**

```
// $JAFF SUB variable1, variable2
template content with $variable1$, $varaible2$ references
// $JAFF END
```

**Available Variables:**

| Variable   | Type | Description                                     |
| ---------- | ---- | ----------------------------------------------- |
| `nspec`    | int  | Number of species in the network                |
| `nreact`   | int  | Number of reactions in the network              |
| `nelem`    | int  | Number of chemical elements in the network      |
| `label`    | str  | Network label/name                              |
| `filename` | str  | Template file name                              |
| `filepath` | Path | Full template file path                         |
| `e_idx`    | int  | Index of electron species (e-) in species array |
| `dedt`     | str  | Language-specific internal energy equation code |

**Examples:**

```cpp
// Insert network constants
// $JAFF SUB nspec, nreact, nelem
#define NSPEC $nspec$
#define NREACT $nreact$
#define NELEM $nelem$
// $JAFF END

// Use network label
// $JAFF SUB label
// Chemical network: $label$
const char* network_name = "$label$";
// $JAFF END

// Reference variable multiple times
// $JAFF SUB nspec
int species_count = $nspec$;
int array_size = $nspec*2$;
double masses[$nspec$];
// $JAFF END
```

Additionally, all integer type substitutions support simple in-place mathematical operations.

```cpp
// $JAFF SUB nspec
int species_count_p1 = $nspec+1$;
int array_size = $nspec*2$;
double masses[$nspec$];
// $JAFF END

// Output
int species_count_p1 = 6;
int array_size = 10;
double masses[5];
```

Supported mathematical operations are

| Token | Operation      |
| ----- | -------------- |
| `+`   | Addition       |
| `-`   | Subtraction    |
| `*`   | Multiplication |
| `/`   | Division       |

---

## REPEAT Command

**Purpose:** Iterate over collections or generate indexed expressions.

The REPEAT command allows the generation of N-D arrays in code. It has 2 formats - horizontal and vertical. If the list of variables doesn't contain `idx`, the array is expanded horizontally.

**Syntax:**

```
// Horizontal format (default when idx not in variable list)
// $JAFF REPEAT variable IN collection $[modifiers]$
template content
// $JAFF END

// Vertical format (when idx is in variable list)
// $JAFF REPEAT idx, variable IN collection $[modifiers]$
template content
// $JAFF END
```

### Horizontal Format

In horizontal format, arrays are expanded inline. The template must contain the variable surrounded by brackets and optional quotes/separators.

**Supported Patterns:**

- Brackets: `[]`, `{}`, `()`, `<>`
- Quotes: `""`, `''`, or none
- Separators: `,`, `;`, `:`, whitespace (default: `, `)

The pattern format is: `{quote}$variable${quote}{separator}` within brackets.

```cpp
// $JAFF REPEAT specie_charge IN specie_charges
double charges[] = {$specie_charge$, };
// $JAFF END
// Output: double charges[] = {0, 0, 1, -1, 0, };

// $JAFF REPEAT charge_truth IN charge_truths
int truth[][] = {$charge_truth$, };
// $JAFF END
// Output: int truth[][] = {{0, 0, 1}, {1, 0, 0}, {0, 1, 1}};
```

### Vertical Format

In vertical format, items are expanded line-by-line with indices. Use `idx` in the variable list to enable vertical expansion. The `idx` variable also doubles down as the array index

```cpp
// ODE expressions
// $JAFF REPEAT idx, ode_expression IN ode_expressions
dydt[$idx$] = $ode_expression$;
// $JAFF END
// Output:
// dydt[0] = -k[0]*y[0];
// dydt[1] = k[0]*y[0] - k[1]*y[1];
// dydt[2] = k[1]*y[1] - k[2]*y[2];

// 2D vertical - Jacobian matrix
// $JAFF REPEAT idx, expr IN jacobian
jac[$idx$, $idx$] = $expr$;
// $JAFF END
// Output:
// jac[1][2] = -nden[0];
// jac[1][3] = nden[0]*tgas;
// jac[2][2] = -nden[1]*nden[0];
// jac[2][3] = nden[1] + tgas*nden[2];
```

The number of `idx` variables apearing in a statement must be equal to the dimension of the array as shown above.

The `idx` variables also support simple offsetting using `+` and `-` operations

```cpp
// $JAFF REPEAT idx, expr IN jacobian
jac[$idx+1$, $idx+2$] = $expr$;
// $JAFF END
// Output:
// jac[1][2] = -nden[0];
// jac[1][3] = nden[0]*tgas;
// jac[2][2] = -nden[1]*nden[0];
// jac[2][3] = nden[1] + tgas*nden[2];
```

Additionally, `rates`, `odes`, `rhses` and `jacobian` supports CSE (Common Subexpression Elemination) substitution.

```cpp
// $JAFF REPEAT idx, expr, cse IN jacobian
const double x$idx$ = $cse$;
jac[$idx+1$, $idx+2$] = $expr$;
// $JAFF END
// Output:
// const double x0 = sqrt(tgas);
// const double x1 = pow(tgas, 2);
// jac[1][2] = -nden[0];
// jac[1][3] = nden[0]*tgas;
// jac[2][2] = -nden[1]*nden[0];
// jac[2][3] = nden[1] + x1\*nden[2];
```

> NOTE: Index offset's don't work for cse variables

**Modifiers:**

An additional modfier list can be specified at the end of the command. The modifier list must be enclosed within `$[]$`

For example:

```cpp
// $JAFF REPEAT idx, specie IN species $[SORT TRUE]$
species_names[$idx$] = "$specie$";
// $JAFF END
```

| Modifier   | Values     | Description                                                   | Supported Collections |
| ---------- | ---------- | ------------------------------------------------------------- | --------------------- |
| `SORT`     | True/False | Sort the array before substitution                            | All                   |
| `USE_DEDT` | True/False | Include/exclude specific internal energy equation in Jacobian | `jacobian`            |

> NOTE: It is not recommended to use the `SORT` modifier for expressions

The general trend of variable naming is the singular version of of the plural collection. For example: For the `odes` collection, the corresponding variable is `ode`

### Expression-Generating Collections

These collections generate mathematical expressions with optional CSE optimization:

| Collection         | Variables                | Description                                      | CSE Support |
| ------------------ | ------------------------ | ------------------------------------------------ | ----------- |
| `rates`            | `idx`, `rate`            | Reaction rate coefficient expressions            | ✓           |
| `odes`             | `idx`, `ode`             | Complete ODE expressions (dydt equations)        | ✓           |
| `rhses`            | `idx`, `rhs`             | Complete RHS expressions (also includes $de/dt$) | ✓           |
| `rhses`            | `idx`, `rhs`             | Right-hand side expressions only                 | ✓           |
| `flux_expressions` | `idx`, `flux_expression` | Flux expressions for each reaction               | ✗           |
| `ode_expressions`  | `idx`, `ode_expression`  | ODE expressions without assignments              | ✗           |
| `jacobian`         | `idx`, `expr`            | Jacobian matrix elements                         | ✓           |

### List-Iterating Collections

These collections iterate over simple data lists:

#### Species Collections

| Collection                     | Variables                     | Description                         |
| ------------------------------ | ----------------------------- | ----------------------------------- |
| `species`                      | `specie`                      | All species names                   |
| `species_with_normalized_sign` | `specie_with_normalized_sign` | Species names with + → j, - removed |
| `specie_masses`                | `specie_mass`                 | Mass of each species                |
| `specie_charges`               | `specie_charge`               | Charge of each species              |
| `specie_masses_ne`             | `specie_mass_ne`              | Masses excluding electrons          |
| `specie_charges_ne`            | `specie_charge_ne`            | Charges excluding electrons         |
| `neutral_species`              | `neutral_specie`              | Neutral species only                |
| `charged_species`              | `charged_specie`              | Charged species only                |
| `neutral_specie_indices`       | `neutral_specie_index`        | Indices of neutral species          |
| `charged_specie_indices`       | `charged_specie_index`        | Indices of charged species          |
| `neutral_specie_indices_ne`    | `neutral_specie_index_ne`     | Neutral indices (no e-)             |
| `charged_specie_indices_ne`    | `charged_specie_index_ne`     | Charged indices (no e-)             |
| `neutral_specie_masses`        | `neutral_specie_mass`         | Masses of neutral species           |
| `charged_specie_masses`        | `charged_specie_mass`         | Masses of charged species           |
| `neutral_specie_masses_ne`     | `neutral_specie_mass_ne`      | Neutral masses (no e-)              |
| `charged_specie_masses_ne`     | `charged_specie_mass_ne`      | Charged masses (no e-)              |
| `charge_truths`                | `charge_truth`                | 1 if charged, 0 if neutral          |
| `charge_truths_ne`             | `charge_truth_ne`             | Charge flags (excluding e-)         |

#### Reaction Collections

| Collection               | Variables              | Description                           |
| ------------------------ | ---------------------- | ------------------------------------- |
| `reactions`              | `reaction`             | All reaction strings                  |
| `reactants`              | `reactant`             | Reactants for each reaction           |
| `products`               | `product`              | Products for each reaction            |
| `photo_reactions`        | `photo_reaction`       | Photoreactions only                   |
| `photo_reaction_indices` | `photo_reaction_index` | Indices of photoreactions             |
| `photo_reaction_truths`  | `photo_reaction_truth` | 1 if photoreaction, 0 otherwise       |
| `tmins`                  | `tmin`                 | Minimum temperature for each reaction |
| `tmaxes`                 | `tmax`                 | Maximum temperature for each reaction |

#### Element Collections

| Collection               | Variables | Description                    |
| ------------------------ | --------- | ------------------------------ |
| `elements`               | `element` | Chemical element symbols       |
| `element_density_matrix` | `element` | Element count per species (2D) |
| `element_truth_matrix`   | `element` | Element presence flags (2D)    |

---

## GET Command

**Purpose:** Access specific properties by name or index.

**Syntax:**

```
// $JAFF GET property FOR argument
```

**Available Properties:**

| Property            | Argument        | Returns | Description                         |
| ------------------- | --------------- | ------- | ----------------------------------- |
| `element_idx`       | element_symbol  | int     | Index of element in element list    |
| `specie_idx`        | specie_name     | int     | Index of species in species array   |
| `reaction_idx`      | reaction_string | int     | Index of reaction in reaction array |
| `specie_mass`       | specie_name     | float   | Mass of specified species           |
| `specie_charge`     | specie_name     | int     | Charge of specified species         |
| `specie_latex`      | specie_name     | str     | LaTeX representation of species     |
| `reaction_tmin`     | reaction_string | float   | Minimum temperature for reaction    |
| `reaction_tmax`     | reaction_string | float   | Maximum temperature for reaction    |
| `reaction_verbatim` | reaction_string | str     | Verbatim reaction string from input |

**Examples:**

```cpp
// Get species properties
// $JAFF GET specie_idx FOR H2
const int h2_idx = $specie_idx$;
// $JAFF END
// $JAFF GET specie_mass FOR H2
const double h2_mass = $specie_mass$;
// $JAFF END
// $JAFF GET specie_charge FOR H2
const int h2_charge = $specie_charge$;
// $JAFF END

// Get element index
// $JAFF GET element_idx FOR C
const int carbon_idx = $element_idx$;
// $JAFF END

// Get reaction properties
// $JAFF GET reaction_tmin FOR H+H2->H2+H
const double reaction_tmin = $reaction_tmin$;

// Use in arrays
double masses[] = {
    // $JAFF GET specie_mass FOR H
    $specie_mass$,
    // $JAFF END
    // $JAFF GET specie_mass FOR H2
    $specie_mass$,
    // $JAFF END
    // $JAFF GET specie_mass FOR O
    $specie_mass$
    // $JAFF END
};

// Inline usage
// $JAFF GET specie_mass FOR H2
printf("H2 mass: %f\n", $specie_mass$);
// $JAFF END
```

---

## HAS Command

**Purpose:** Returns if the property exists or not in the form of 0 or 1

**Syntax:**

```
// $JAFF HAS property argument
content to include if property exists
// $JAFF END
```

**Available Properties:**

| Property   | Argument        | Returns | Description                        |
| ---------- | --------------- | ------- | ---------------------------------- |
| `specie`   | specie_name     | int     | True if species exists in network  |
| `reaction` | reaction_string | int     | True if reaction exists in network |
| `element`  | element_symbol  | int     | True if element exists in network  |

**Examples:**

```cpp
// Include code only if electron exists
// $JAFF HAS specie e-
int has_e = $specie$
// $JAFF END
if (has_e) {
  void compute_electron_density(double* abundances) {
      // $JAFF GET specie_idx FOR e-
      int e_idx = $specie_idx$;
      // $JAFF END
      return abundances[e_idx];
  }
}
```

---

## REDUCE Command

**Purpose:** Generate reduction/summation expressions over collections.

**Syntax:**

```
// $JAFF REDUCE variable1, variable2 IN collection1, colleciton2
expression using $($variable1$, $variable2$)$
// $JAFF END
```

The expression to be reduced must be presented within `$()$`. Please refer to the examples below

**Available Collections:**

| Collection                  | Variable                   | Description                         |
| --------------------------- | -------------------------- | ----------------------------------- |
| `specie_charges`            | `specie_charge`            | Sum charges of all species          |
| `specie_masses`             | `specie_mass`              | Sum masses of all species           |
| `specie_charges_ne`         | `specie_charge_ne`         | Sum charges (excluding e-)          |
| `specie_masses_ne`          | `specie_mass_ne`           | Sum masses (excluding e-)           |
| `charged_specie_charges`    | `charged_specie_charge`    | Sum charges of charged species only |
| `charged_specie_charges_ne` | `charged_specie_charge_ne` | Sum charges of ions (no e-)         |
| `charge_truths`             | `charge_truth`             | Count charged species               |
| `charge_truths_ne`          | `charge_truth_ne`          | Count charged species (no e-)       |
| `photo_reaction_truths`     | `photo_reaction_truth`     | Count photoreactions                |
| `photo_reaction_indices`    | `photo_reaction_index`     | Sum photoreaction indices           |
| `tmins`                     | `tmin`                     | Process all Tmin values             |
| `tmaxes`                    | `tmax`                     | Process all Tmax values             |
| `neutral_specie_indices`    | `neutral_specie_index`     | Process neutral species indices     |
| `charged_specie_indices`    | `charged_specie_index`     | Process charged species indices     |
| `neutral_specie_indices_ne` | `neutral_specie_index_ne`  | Process neutral indices (no e-)     |
| `charged_specie_indices_ne` | `charged_specie_index_ne`  | Process charged indices (no e-)     |
| `neutral_specie_masses`     | `neutral_specie_mass`      | Process neutral masses              |
| `charged_specie_masses`     | `charged_specie_mass`      | Process charged masses              |
| `neutral_specie_masses_ne`  | `neutral_specie_mass_ne`   | Process neutral masses (no e-)      |
| `charged_specie_masses_ne`  | `charged_specie_mass_ne`   | Process charged masses (no e-)      |

**Examples:**

```cpp
// Single variable reduction - sum of charges
// $JAFF REDUCE specie_charge IN specie_charges
const double total_charge = $($specie_charge$)$;
// $JAFF END
// Output: const double total_charge = -1.0 + 1.0 + 0.0 + 0.0;

// Single variable reduction - sum of masses
// $JAFF REDUCE specie_mass IN specie_masses_ne
const double total_mass = $($specie_mass$)$;
// $JAFF END
// Output: const double total_mass = 1.008 + 2.016 + 15.999;

// Multiple variable reduction - electron density from charge balance
// $JAFF REDUCE charged_specie_index_ne, charged_specie_charge_ne IN charged_specie_indices_ne, charged_specie_charges_ne
state.xn[e_idx] = $($charged_specie_charge_ne$*state.xn[$charged_specie_index_ne$])$;
// $JAFF END
// Output: state.xn[e_idx] = 1*state.xn[2] + -1*state.xn[5] + 2*state.xn[7];

// Complex expression with multiple variables
// $JAFF REDUCE neutral_specie_index, mass IN neutral_specie_indices, neutral_specie_masses
const double neutral_mass = $($mass$ * y[$neutral_specie_idx$])$;
// $JAFF END
// Output: const double neutral_mass = 1.008 * y[0] + 2.016 * y[1] + 15.999 * y[3];
```

> NOTE: Any number of collections can be reduced provided they have the same length

---

## REPLACE Directive

**Purpose:** Apply regex-based text replacement to generated output.

Probably the most powerful feature in JAFF templating, anything form the output expression can be replaced by the `REPLACE` directive. This can be used to transmute the output into unsupported languages and perform even more complicated operatotions. The REPLACE directive is supported by all commands and it must be included in the modifiers list.

**Features:**

- REPLACE directives must be enclosed in `$[...]$`
- Applied **after** code generation
- Supports Python regex syntax
- Supports capture groups and backreferences (`\1`, `\2`, etc.)
- Multiple REPLACE directives can be chained
- Applied sequentially in order specified
- Automatically reset at `$JAFF END`

**Syntax:**

```
// $JAFF COMMAND arguments $[REPLACE pattern1 replacement1 ... other modifers]
content
// $JAFF END

// $JAFF COMMAND arguments $[REPLACE pattern1 replacement1 REPLACE pattern2 replacement2 ... other modifiers]
content
// $JAFF END
```

**Examples:**

```cpp
// Sanitize species names (+ and - to valid identifiers)
// $JAFF REPEAT idx, specie IN species $[REPLACE \+ _plus REPLACE - _minus]
const int idx_$specie$ = $idx$;
// $JAFF END
// Output:
// const int idx_H_plus = 0;   // H+ -> H_plus
// const int idx_e_minus = 1;  // e- -> e_minus

// Regex with capture groups
// $JAFF REPEAT idx, specie IN species $[REPLACE H_(\d+) Hydrogen_\1 REPLACE He Helium]
species[$idx$] = "$specie$";
// $JAFF END
// Output:
// species[0] = "Hydrogen_1";  // H_1 -> Hydrogen_1
// species[1] = "Hydrogen_2";  // H_2 -> Hydrogen_2
// species[2] = "Helium";      // He -> Helium
```

**Common Use Cases:**

- Sanitize names: Convert special characters to valid identifiers
- Replace keywords: Change language keywords
- Add prefixes/suffixes: Transform identifiers with patterns
- Normalize formats: Convert naming conventions
- Unsupported language: Generate syntax for unsupported language

---

A list of pre-made templates are available at `src/jaff/templates/generator`

## Troubleshooting

## See Also

- [jaffgen Command Reference](jaffgen-command.md) - Complete command-line interface documentation
- [Custom code generation](code-generation.md) - Learn about CSE and optimization

---
