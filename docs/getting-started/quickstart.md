---
tags:
    - Introduction
icon: lucide/rocket
---

# Quick Start Guide

## Analysing networks

Let's load and explore a chemical reaction network and see how we can extract its properties. A `Network` forms the backbone of **JAFF** and represents all the chemical reactions taking place in a specified scenario along with their associated properties.

### Step 1: Loading a Network

Loading a network requires a network file. Currently JAFF supports network files in the following formats: `KIDA`, `KROME`, `PRIZMO`, `UCLCHEM`, and `UDFA`.

```python
from jaff import Network

# Load a network file
net = Network("networks/demos/demo1.jet")
```

Once the network is loaded, different properties of the network can be accessed using the `net` object.

```python
# Display basic information
print(f"Network label: {net.label}")
print(f"Number of species: {net.species.count}")
print(f"Number of reactions: {net.reactions.count}")
```

**Output**:

```
Network label: demo1
Number of species: 14
Number of reactions: 15
```

### Step 2: Exploring Species

The network contains a species attribute that holds information about all the species taking part in the reaction network.

```python
# List first 5 species
for i, species in enumerate(net.species[:5]):
    print(f"{i}: {species.name} (mass={species.mass:.5e} gm, charge={species.charge})")
```

**Output**:

```
0: H+ (mass=1.67377e-24 gm, charge=1)
1: e- (mass=9.10938e-28 gm, charge=-1)
2: H (mass=1.67377e-24 gm, charge=0)
3: C (mass=1.99447e-23 gm, charge=0)
4: C+ (mass=1.99447e-23 gm, charge=1)
```

### Step 3: Exploring Reactions

The network also contains a reactions attribute that holds information about all reactions that are part of the network.

```python
# Display first 3 reactions
for i, reaction in enumerate(net.reactions[:3]):
    print(f"{i}: {reaction.verbatim}")
```

**Output**:

```
0: H+ + e- -> H
1: H -> H+ + e-
2: C -> C+ + e-
```

A detailed overview of the network and its attributes and methods is provided by the [user guide](../user-guide/loading-networks.md) and the [api reference](../api/index.md).

## Generating Code

Now let's generate code for solving the chemical network.

### Step 1: Creating a Template

A template is a file that contains `JAFF directives` which are later processed by JAFF. Create a file named `rates.cpp`:

```cpp
// rates_template.cpp
#include <cmath>

// $JAFF SUB nreact
const int NUM_REACTIONS = $nreact$;
// $JAFF END

// Calculate reaction rates
void compute_rates(double* rate, const double* n, const double* k, double T) {
    // $JAFF REPEAT idx, rate IN rates
    rate[$idx$] = $rate$;
    // $JAFF END
}

// Reaction names
// $JAFF REPEAT idx, reaction IN reactions
const char* reaction_names[$idx$] = "$reaction$";
// $JAFF END
```

### Step 2: Generating Code

Once the template is ready, you can use the `jaffgen` command to generate the code.

```bash
jaffgen --network networks/demos/demo1.jet --files path/to/rates.cpp
```

The generated file will be located in the `generated` folder at the root of the project.

### Step 3: View Generated Code

The generated `rates.cpp` will contain:

```cpp
#include <cmath>

const int NUM_REACTIONS = 15;

void compute_rates(double* rate, const double* n, const double* k, double T) {
    rate[0] = ...  // H+ + e- -> H
    rate[1] = ...  // H -> H+ + e-
    rate[2] = ...  // C -> C+ + e-
    // ... more rates
}

const char* reaction_names[0] = "H+ + e- -> H";
const char* reaction_names[1] = "H -> H+ + e-";
const char* reaction_names[2] = "C -> C+ + e-";
// ... more names
```

**Supported languages:** `c`, `cxx` , `fortran` , `python` , `rust` , `julia` and `r`

## Next Steps

Now that you've completed the quick start:

1. **Learn the Basics**: Read about [Basic Concepts](concepts.md) to understand chemical networks
2. **User Guide**: Explore the detailed [User Guide](../user-guide/loading-networks.md)
3. **Templates**: Understand [Template Syntax](../user-guide/template-syntax.md) for custom code generation
4. **API Reference**: Browse the complete [API documentation](../api/index.md)

## Getting Help

- **Documentation**: Browse the full documentation
- **Examples**: Check the `examples/` directory in the repository
- **Issues**: Report bugs at [GitHub Issues](https://github.com/tgrassi/jaff/issues)
- **Discussions**: Ask questions in GitHub Discussions

## Tips & Tricks

<!-- prettier-ignore -->
!!! tip "Pro Tip: Species Lookup"
    Use the species and reactions lookup instead of looping to find a species or reactions object:
    `idx = net.species["CO"]  # Much faster than searching`

<!-- prettier-ignore -->
!!! tip "Pro Tip: Template Testing"
    Test templates on small networks first before using large ones:

```bash
    jaffgen --indir folder --network networks/demos/demo1.jet
```

<!-- prettier-ignore -->
!!! warning "Watch Out: File Extensions"
    The parser determines language from file extension: - `.cpp`, `.cxx`, `.cc` → C++ - `.c` → C - `.f90`, `.f95` → Fortran

    **Make sure your template has the correct extension!**

## Example Networks

JAFF comes with several predefined networks:

- `networks/demos` - Small test networks
- `networks/COthin` - CO chemistry
- `networks/GOW` - Gong-Ostriker-Wolfire chemical network
