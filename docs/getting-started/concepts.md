---
tags:
    - Introduction
icon: lucide/layers
---

# Basic Concepts

The main aim of jaff is to provide a common interface for all common chemical network formats and it doubles down as a code generator. It is also the first code to completely support explicit photochemistry code generation

## Core Components

### 1. Chemical Networks

A **chemical network** describes a system of chemical species and the reactions between them.

**Example Network:**

The following network describes a simple collisonal hydrogen ionization and recommbination network

```text
H -> H+ + e-
H+ + e- -> H
```

This network has:

- 3 species: H, H+ and e-
- 2 reactions
- Temperature-dependent rate coefficients

A rate coefficient tells us how fast the reaction occurs.
For a reaction of the form

$$ \alpha A + \beta B -> \gamma C $$

where $\alpha$, $\beta$ and $\gamma$ are the stoichiometric coefficients, the rate of the reaction is given by

$$ r = k\ [A]^{\alpha} [B]^{\beta} $$

where $k$ is the rate coefficient and $[A]$ and $[B]$ represents the concentrations of $A$ and $B$ respectively.

In astrophysics, reactions can occur due to a lot of reasons. For example, a reaction can occur due to thermal collisions, collisions with cosmic ray particles, photons from various astrophysical sources or simply a spontaenous decay. All these reactions typically have different characterstic and rates and the cause of the reaction can significantly alter the environment.

### 2. Network Object

The `Network` class represents a loaded chemical network in memory.

```python
from jaff import Network

# Load a network file
net = Network("networks/COthin/react_COthin.jet")

# Access properties
print(f"Species: {len(net.species)}")      # Number of species
print(f"Reactions: {len(net.reactions)}")  # Number of reactions
print(f"Label: {net.label}")                # Network identifier
```

**It contains:**

- `species`: Collection of all chemical species; supports name lookup via `net.species["name"]`
- `reactions`: Collection of all reactions
- Mass information and elemental composition
- `file_name`: The network file name
- `label`: A label for the network

### 3. Species

A **species** represents a single chemical entity with properties.

```python
# Get a species
species = net.species[0]

print(f"Name: {species.name}")        # e.g., "CO"
print(f"Mass: {species.mass}")        # Atomic mass in amu
print(f"Charge: {species.charge}")    # Electric charge
print(f"Index: {species.index}")      # Position in array
```

**Species Properties:**

- `name`: Chemical formula or identifier
- `mass`: Molecular mass in atomic mass units
- `charge`: Electric charge (0 for neutral, +1/-1 for ions)
- `index`: Position in the species array (for indexing)
- `latex`: Latex representation of the species

### 4. Reactions

A **reaction** describes a chemical transformation.

```python
# Get a reaction
reaction = net.reactions[0]

print(f"Reaction: {reaction.verbatim}")  # e.g., "H + O -> OH"
print(f"Type: {reaction.rtype}")         # Reaction type

# Get reaction rate
k = reaction.rate
print(f"Rate: {k}")
```

**Reaction Components:**

- `reactants`: Species consumed in the reaction
- `products`: Species created in the reaction
- `rate`: Formula for calculating reaction speed as a sympy expresssion
- `rtype`: Classification (e.g. photo)
- `tmin`: Minimum temperature for reaction cutoff
- `tmax`: Maximum temperature for reaction cutoff
- `verbatim`: User friendly representation of reaction

**Rate Expressions:**

Most reactions use Arrhenius-type rate laws:

$$k(T) = \alpha \left(\frac{T}{300}\right)^\beta e^{-\gamma/T}$$

Where:

- $\alpha$: Pre-exponential factor
- $\beta$: Temperature exponent
- $\gamma$: Activation energy parameter
- $T$: Temperature in Kelvin

### 5. Code Generation

JAFF uses **templates** to generate code in multiple languages.

**Template Workflow:**

1. **Write a template** with the `$JAFF` commands
2. **Process the template** with the network
3. **Generate code** in your target language

**Example Template:**

```cpp hl_lines="2 4"
// Template: rates.cpp
// $JAFF SUB nreact
const int NREACT = $nreact$;
// $JAFF END

void compute_rates(double* k, double T) {
    $JAFF REPEAT idx, rate IN rates
    k[$idx$] = $rate$;
    $JAFF END
}
```

**Generated Code:**

```cpp
const int NREACT = 127;

void compute_rates(double* k, double T) {
    k[0] = 1.2e-10 * pow(T/300, 0.5);
    k[1] = 3.4e-11 * exp(-500/T);
    // ... more rates
}
```

## Key Concepts

### Network Files

JAFF supports multiple network file formats:

- **KIDA format**: From the KInetic Database for Astrochemistry
- **UDFA format**: From the UMIST Database for Astrochemistry
- **PRIZMO format**: From the PRIZMO astrochemical code
- **KROME format**: From the KROME package for astrochemistry
- **UCLCHEM format**: From the UCL Chemistry and Dust code

### Array Indexing

Different languages use different indexing conventions and bracket formats:

| Language | Starting Index | Example  |
| -------- | -------------- | -------- |
| C/C++    | 0              | `arr[0]` |
| Python   | 0              | `arr[0]` |
| Fortran  | 1              | `arr(1)` |

JAFF handles these differences automatically when generating code.

### Index Offsets

You can customize array indexing:

```python
from jaff import Codegen

cg = Codegen(network=net, lang="c++")

# Use default offset (0 for C++)
code1 = cg.get_rates_str(idx_offset=0)  # arr[0], arr[1], ...

# Use custom offset (e.g., start at 1)
code2 = cg.get_rates_str(idx_offset=1)  # arr[1], arr[2], ...
```

### Common Subexpression Elimination (CSE)

CSE is an optimization that reduces redundant calculations:

**Without CSE:**

```cpp
rate[0] = k0 * sqrt(T) * n[0];
rate[1] = k1 * sqrt(T) * n[1];
rate[2] = k2 * sqrt(T) * n[2];
```

**With CSE:**

```cpp
double x0 = sqrt(T);
rate[0] = k0 * x0 * n[0];
rate[1] = k1 * x0 * n[1];
rate[2] = k2 * x0 * n[2];
```

Enable CSE with `use_cse=True`:

```python
code = cg.get_rates_str(use_cse=True)  # More efficient
```

### ODEs (Ordinary Differential Equations)

Chemical networks produce systems of ODEs describing concentration changes:

$$\frac{dy_i}{dt} = \sum_j \nu_{ij} R_j$$

Where:

- $y_i$: Concentration of species i
- $R_j$: Rate of reaction j
- $\nu_{ij}$: Stoichiometric coefficient ($y_{i}^{c_{j}}$)

JAFF generates these ODEs automatically:

```python
ode_code = cg.get_ode_str(ode_var="dydt", use_cse=True)
```

### Jacobian Matrix

The **Jacobian** is the matrix of partial derivatives:

$$J_{ij} = \frac{\partial f_i}{\partial y_j}$$

Where $f_i = dy_i/dt$ is the ODE for species i.

Jacobians are essential for implicit ODE solvers:

```python
jac_code = cg.get_jacobian_str(jac_var="J", use_cse=True)
```

### Element Conservation

Chemical reactions conserve elements. JAFF can check conservation:

```python
elem = net.elements

# Get element truth matrix (rows=elements, cols=species; entry [i][j] = 1 if present)
# Note: use density_matrix() for atom counts
density_matrix = elem.density_matrix()
```

## Workflow Examples

### Basic Analysis Workflow

```python
from jaff import Network

# 1. Load network
net = Network("networks/COthin/react_COthin.jet")

# 2. Explore species
for species in net.species:
    print(f"{species.name}: {species.mass} amu")

# 3. Explore reactions
for reaction in net.reactions:
    print(f"{reaction.verbatim}: {reaction.rtype}")

# 4. Get rates for further calculation and plotting
for reaction in net.reactions[:5]:
    k = reaction.rate
    print(f"{reaction.verbatim}: k = {k}")
```

### Code Generation Workflow with Preprocessor

The recommended workflow uses the `Preprocessor` class to replace pragmas in template files:

```python
from jaff import Network, Codegen, Preprocessor

# 1. Load network
net = Network("networks/COthin/react_COthin.jet")

# 2. Create code generator and preprocessor
cg = Codegen(network=net, lang="cxx")
p = Preprocessor()

# 3. Generate code components
commons = cg.get_commons(idx_offset=0, definition_prefix="static constexpr int ")
rates = cg.get_rates_str(idx_offset=0, use_cse=True)
odes = cg.get_ode_str(idx_offset=0, use_cse=True)
jacobian = cg.get_jacobian_str(idx_offset=0, use_cse=True)

# 4. Define pragma replacements
replacements = {
    "COMMONS": commons,
    "RATES": rates,
    "ODE": odes,
    "JACOBIAN": jacobian,
    "NUM_SPECIES": f"static constexpr int neqs = {net.species.count};"
}

# 5. Process template file with pragma replacement
# Template file should contain pragmas like: // PREPROCESS_RATES
p.preprocess(
    path="path/to/templates",
    fnames=["chemistry.hpp"],
    dictionaries=replacements,
    comment="//",  # or use "auto" for auto-detection
    path_build="output/"
)
```

In your template file (`chemistry.hpp`), use pragma markers:

```cpp
// PREPROCESS_COMMONS
// PREPROCESS_END

void compute_rates() {
    // PREPROCESS_RATES
    // PREPROCESS_END
}

void compute_ode(double* y, double* dydt) {
    // PREPROCESS_ODE
    // PREPROCESS_END
}
```

The preprocessor will replace content between `// PREPROCESS_<KEY>` and `// PREPROCESS_END` with the corresponding values from the dictionary.

````

### Template-Based Workflow

Use the `jaffgen` CLI to process template files with `$JAFF` directives:

```bash
jaffgen --network networks/COthin/react_COthin.jet --files template.cpp
```

The generated file is placed in the `generated/` folder. See [Template Syntax](../user-guide/template-syntax.md) for directive reference.
````

## Best Practices

### 1. Validate Networks

Always check for errors when loading:

```python
net = Network("mynetwork.dat", errors=True)
```

This enables warnings for:

- Missing sink/source species
- Duplicate reactions
- Isomer issues
- Element conservation violations

### 2. Use CSE for Performance

Enable CSE for production code:

```python
cg.get_rates_str(use_cse=True)  # Faster execution
```

### 3. Check Generated Code

Always review generated code before using:

```python
code = cg.get_rates_str()
print(code)  # Inspect output
```

### 4. Choose Appropriate Index Offsets

Match your target framework:

```python
# For C/C++/Python: start at 0
code = cg.get_rates_str(idx_offset=0)

# For Fortran: start at 1
code = cg.get_rates_str(idx_offset=1)

# For custom arrays: use any offset
code = cg.get_rates_str(idx_offset=5)
```

### 5. Organize Generated Code

Structure your output logically:

```python
# Generate all components
commons = cg.get_commons()
rates = cg.get_rates_str(use_cse=True)
odes = cg.get_ode_str(use_cse=True)
jac = cg.get_jacobian_str(use_cse=True)

# Combine in logical order
full_code = f"""
// Common definitions
{commons}

// Rate calculations
{rates}

// ODE system
{odes}

// Jacobian matrix
{jac}
"""
```

## Next Steps

Now that you understand the basic concepts:

2. [Loading Networks](../user-guide/loading-networks.md): Learn about network file formats
3. [Code Generation](../user-guide/code-generation.md): Master code generation
4. [Template Syntax](../user-guide/template-syntax.md): Create custom templates
5. [API Reference](../api/index.md): Explore the complete API

## Common Terms

| Term                 | Definition                                                      |
| -------------------- | --------------------------------------------------------------- |
| **Species**          | A chemical entity (atom, molecule, ion)                         |
| **Reaction**         | A chemical transformation between species                       |
| **Rate Coefficient** | Function determining reaction speed                             |
| **Stoichiometry**    | Ratio of reactants to products                                  |
| **ODE**              | Ordinary Differential Equation describing concentration changes |
| **Jacobian**         | Matrix of partial derivatives of ODEs                           |
| **CSE**              | Common Subexpression Elimination (optimization)                 |
| **Template**         | File with JAFF commands for code generation                     |
| **Network**          | Collection of species and reactions                             |
| **Index Offset**     | Starting index for arrays (0 or 1)                              |

## Further Reading

- **Chemistry Background**: Understanding chemical kinetics helps interpret results
- **ODE Solvers**: Learn about numerical integration methods
- **Programming Languages**: Familiarity with target languages (C++, Fortran, etc.)
- **SymPy**: JAFF uses SymPy for symbolic mathematics
