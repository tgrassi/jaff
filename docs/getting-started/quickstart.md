---
tags:
    - Introduction
icon: lucide/rocket
---

# Quick Start Guide

## Prerequisites

Make sure you have :fontawesome-brands-python: Python `>=3.9` installed:

```bash
python --version
```

## Installation

From source:

```bash
git clone https://github.com/tgrassi/jaff.git
cd jaff
pip install -e .
```

## Your First Network

Let's load and explore a chemical reaction network.

### Step 1: Load a Network

```python
from jaff import Network

# Load a network file
net = Network("networks/react_COthin")

# Display basic information
print(f"Network label: {net.label}")
print(f"Number of species: {len(net.species)}")
print(f"Number of reactions: {len(net.reactions)}")
```

**Output**:

```
Network label: react_COthin
Number of species: 35
Number of reactions: 127
```

### Step 2: Explore Species

```python
# List first 5 species
for i, species in enumerate(net.species[:5]):
    print(f"{i}: {species.name} (mass={species.mass:.2f} amu, charge={species.charge})")
```

**Output**:

```
0: H (mass=1.01 amu, charge=0)
1: H2 (mass=2.02 amu, charge=0)
2: C (mass=12.01 amu, charge=0)
3: O (mass=16.00 amu, charge=0)
4: CO (mass=28.01 amu, charge=0)
```

### Step 3: Explore Reactions

```python
# Display first 3 reactions
for i, reaction in enumerate(net.reactions[:3]):
    print(f"{i}: {reaction.verbatim}")
```

**Output**:

```
0: H + O -> OH
1: H2 + O -> OH + H
2: C + O2 -> CO + O
```

## Generating Code

Now let's generate code for rate calculations.

### Step 1: Create a Template

Create a file named `rates_template.cpp`:

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

### Step 2: Generate Code

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

# Load network
net = Network("networks/react_COthin")

# Parse template
parser = Fileparser(net, Path("rates_template.cpp"))
output = parser.parse_file()

# Save output
with open("rates.cpp", "w") as f:
    f.write(output)

print("Generated rates.cpp!")
```

### Step 3: View Generated Code

The generated `rates.cpp` will contain:

```cpp
#include <cmath>

const int NUM_REACTIONS = 127;

void compute_rates(double* rate, const double* n, const double* k, double T) {
    rate[0] = ...  // H + O -> OH
    rate[1] = ...  // H2 + O -> OH + H
    rate[2] = ...  // C + O2 -> CO + O
    // ... more rates
}

const char* reaction_names[0] = "H + O -> OH";
const char* reaction_names[1] = "H2 + O -> OH + H";
const char* reaction_names[2] = "C + O2 -> CO + O";
// ... more names
```

## Using the Command Line

You can also use the CLI for quick code generation without writing Python scripts:

### Basic Usage

**Using the installed command:**

```bash
jaffgen --network networks/react_COthin --files rates_template.cpp --outdir output/
```

This creates `output/rates_template.cpp` with the generated code.

### Using Predefined Templates

JAFF supports predefined template collections:

```bash
# Use a predefined template collection
jaffgen --network networks/react_COthin --template kokkos_ode --outdir output/
```

This processes all files in the `jaff/templates/generator/chemistry_solver/` directory.

### Processing Multiple Files

```bash
# Process all templates in a directory
jaffgen --network networks/react_COthin --indir templates/microphysic --outdir output/

# Process multiple specific files
jaffgen --network networks/react_COthin --files template1.cpp template2.f90 model.py --outdir output/

# Process multiple specific files and folders
jaffgen --network networks/react_COthin --indir templates/microphysics --files template1.cpp template2.f90 model.py --outdir output/
```

### Specifying Language

For files with non-standard extensions, specify a default language:

```bash
# Generate Rust code from a text template
jaffgen --network networks/react_COthin --files template.txt --lang rust --outdir output/

# Generate Julia code
jaffgen --network networks/react_COthin --files custom.template --lang julia --outdir output/
```

You will need to provide the language if you are using the `--indir` and the input directory contains unsupported files

**Supported languages:** `c`, `cxx` , `fortran` , `python` , `rust` , `julia` and `r`

## Common Use Cases

### 1. List All Species

```python
from jaff import Network

net = Network("networks/react_COthin")

print("All species:")
for species in net.species:
    print(f"  {species.name}")
```

### 2. Find Species by Name

```python
from jaff import Network

net = Network("networks/react_COthin")

# Get species index
co_index = net.specie_index["CO"]
co = net.species[co_index]

print(f"CO: index={co_index}, mass={co.mass}, charge={co.charge}")
```

### 3. View rate

```python
from jaff import Network

net = Network("networks/react_COthin")

# Get first reaction
reaction = net.reactions[0]

k = reaction.rate

print(f"Rate coefficient: {k}")
```

### 4. Check Element Properties

```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)

print(f"Network contains {elem.nelems} elements:")
print(elem.elements)

# Get element density matrix
density = elem.get_element_density_matrix()
print(f"\nElement density matrix shape: {len(density)} x {len(density[0])}")
```

### 5. Generate ODEs

Create `odes_template.cpp`:

```cpp
// $JAFF SUB nspec
const int NUM_SPECIES = $nspec$;
// $JAFF END

void compute_odes(double* dydt, const double* y, const double* rate) {
    // Initialize to zero
    for (int i = 0; i < NUM_SPECIES; i++) {
        dydt[i] = 0.0;
    }

    // $JAFF REPEAT idx, ode IN odes
    dydt[$idx$] += $ode$;
    // $JAFF END
}
```

Generate the code:

```python
from jaff import Network
from jaff.file_parser import Fileparser
from pathlib import Path

net = Network("networks/react_COthin")
parser = Fileparser(net, Path("odes_template.cpp"))
output = parser.parse_file()

with open("odes.cpp", "w") as f:
    f.write(output)
```

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

!!! tip "Pro Tip: Network Validation"
Always check your network for errors when loading:
`python
    net = Network("networks/mynetwork.dat", errors=True)
    `

!!! tip "Pro Tip: Species Lookup"
Use the species dictionary for fast lookups:
`python
    idx = net.specie_dict["CO"]  # Much faster than searching
    `

!!! tip "Pro Tip: Template Testing"
Test templates on small networks first before using large ones:

```python
    # Use a small test network
    net = Network("networks/test.dat")
    parser = Fileparser(net, Path("template.cpp"))
    print(parser.parse_file())  # Check output
```

!!! warning "Watch Out: File Extensions"
The parser determines language from file extension: - `.cpp`, `.cxx`, `.cc` → C++ - `.c` → C - `.f90`, `.f95` → Fortran

    Make sure your template has the correct extension!

## Example Networks

JAFF comes with several example networks:

- `networks/test.dat` - Small test network
- `networks/react_COthin` - CO chemistry
- `networks/gas_reactions_kida.uva.2024.in` - KIDA format

Try them out:

```python
from jaff import Network

# Try different networks
networks = [
    "networks/test.dat",
    "networks/react_COthin",
]

for network_file in networks:
    net = Network(network_file)
    print(f"{network_file}: {len(net.species)} species, {len(net.reactions)} reactions")
```
