---
tags:
    - Api
    - Network
icon: lucide/git-compare-arrows
---

# Network

The `Network` class is the core of JAFF, representing a chemical reaction network loaded from a file.

## Overview

The `Network` class loads and validates chemical reaction networks, providing access to species, reactions, and network properties. It automatically parses various network file formats and validates the network structure.

```python
from jaff import Network

# Load a network
net = Network("networks/react_COthin")

# Access properties
print(f"Species: {len(net.species)}")
print(f"Reactions: {len(net.reactions)}")
print(f"Label: {net.label}")
```

## Class Reference

```python
class Network:
    """
    Main class for chemical reaction networks.

    Attributes:
        label (str): Network name/identifier
        species (list): List of Species objects
        reactions (list): List of Reaction objects
        fname (str): Source filename
        rates (dict): Rate constants dictionary
    """
```

The network class contains the following properties:

`get_number_of_species`,
`get_species_index`,
`get_species_object`,
`get_reaction_index`,
`get_reaction_by_verbatim`,
`get_sfluxes`,
`get_sodes`,
`compare_reactions`,
`compare_species`,
`check_sink_sources`,
`check_recombinations`,
`check_isomers`,
`check_unique_reactions`,

## Constructor

### `Network()`

Create a Network object by loading a chemical reaction network file.

**Parameters:**

- `fname` (str): Path to the network file
- `errors` (bool): If True, raise exceptions on validation errors. Default: False
- `label` (str): Custom label for the network. Default: filename without extension
- `funcfile` (str): Path to auxiliary function file for custom rate expressions. Default: None
- `replace_nH` (bool): Replace hydrogen nuclei density expressions. Default: True

**Returns:**

- `Network`: Initialized network object

**Raises:**

- `FileNotFoundError`: If network file doesn't exist
- `ValueError`: If network file format is invalid
- `Exception`: If errors=True and network has validation issues

**Example:**

```python
from jaff import Network

# Basic usage
net = Network("networks/react_COthin")

# With error checking
net = Network("networks/mynetwork.dat", errors=True)

# With custom label
net = Network("networks/react_COthin", label="CO_chemistry")

# With auxiliary functions
net = Network("networks/react_COthin", funcfile="aux_funcs.txt")
```

## Attributes

### Core Attributes

| Attribute        | Type                                           | Description                                     |
| ---------------- | ---------------------------------------------- | ----------------------------------------------- |
| `species`        | `list[Species]`                                | List of all species in the network              |
| `reactions`      | `list[Reaction]`                               | List of all reactions in the network            |
| `species_dict`   | `dict[str, int]`                               | Dictionary mapping species names to indices     |
| `reactions_dict` | `dict[str, int]`                               | Dictionary mapping reaction verbatim to indices |
| `label`          | `str`                                          | Network identifier/label                        |
| `file_name`      | `str`                                          | Path to the original network file               |
| `mass_dict`      | `dict[str, [dict["name": str], "mass": float]` | Atomic mass dictionary                          |
| `rlist`          | `np.ndarray`                                   | Reactant matrix (nreact × nspec)                |
| `plist`          | `np.ndarray`                                   | Product matrix (nreact × nspec)                 |

### Energy Attributes

| Attribute    | Type         | Description              |
| ------------ | ------------ | ------------------------ |
| `dEdt_chem`  | `sympy.Expr` | Chemical energy equation |
| `dEdt_other` | `sympy.Expr` | Other energy terms       |

### Photochemistry

| Attribute        | Type             | Description            |
| ---------------- | ---------------- | ---------------------- |
| `photochemistry` | `Photochemistry` | Photochemistry handler |

## Methods

### Species Access Methods

#### `get_number_of_species()`

Get the total number of species in the network.

**Returns:**

- `int`: Number of species

**Example:**

```python
nspec = net.get_number_of_species()
print(f"Network has {nspec} species")
```

#### get_species_index()

Get the array index of a species by name.

**Parameters:**

- `name` (str): Species name

**Returns:**

- `int`: Species index in the species array

**Raises:**

- `KeyError`: If species name not found

**Example:**

```python
idx = net.get_species_index("CO")
print(f"CO is at index {idx}")
```

#### get_species_object()

Get the Species object by name.

**Parameters:**

- `name` (str): Species name

**Returns:**

- `Species`: The species object

**Raises:**

- `KeyError`: If species name not found

**Example:**

```python
co = net.get_species_object("CO")
print(f"Mass: {co.mass}, Charge: {co.charge}")
```

### Reaction Access Methods

#### get_reaction_index()

Get the array index of a reaction by its verbatim string.

**Parameters:**

- `name` (str): Reaction verbatim (e.g., "H + O -> OH")

**Returns:**

- `int`: Reaction index

**Raises:**

- `KeyError`: If reaction not found

**Example:**

```python
idx = net.get_reaction_index("H + O -> OH")
print(f"Reaction is at index {idx}")
```

#### `get_reaction_by_verbatim()`

Get a Reaction object by its verbatim string.

**Parameters:**

- `verbatim` (str): Reaction string (e.g., "H + O -> OH")
- `rtype` (str): Optional reaction type filter. Default: None

**Returns:**

- `Reaction` or `None`: The matching reaction or None if not found

**Example:**

```python
reaction = net.get_reaction_by_verbatim("H + O -> OH")
if reaction:
    print(f"Rate type: {reaction.rtype}")
```

#### get_reaction_verbatim()

Get the verbatim string representation of a reaction.

**Parameters:**

- `idx` (int): Reaction index

**Returns:**

- `str`: Reaction verbatim string

**Example:**

```python
verbatim = net.get_reaction_verbatim(0)
print(f"First reaction: {verbatim}")
```

### Symbolic Expression Methods

#### `get_sfluxes()`

Get symbolic expressions for reaction fluxes.

**Returns:**

- `list[sympy.Expr]`: List of flux expressions for each species

**Description:**

Returns the net flux for each species from all reactions as symbolic SymPy expressions. These represent the rate of change of each species concentration.

**Example:**

```python
fluxes = net.get_sfluxes()
for i, flux in enumerate(fluxes[:3]):
    print(f"Species {i} flux: {flux}")
```

#### `get_sodes()`

Get symbolic ordinary differential equations for the network.

**Returns:**

- `list[sympy.Expr]`: List of ODE expressions (dn_i/dt) for each species

**Description:**

Returns the complete ODE system as symbolic SymPy expressions. These can be used for symbolic manipulation or code generation.

**Example:**

```python
odes = net.get_sodes()
for i, ode in enumerate(odes[:3]):
    print(f"dn_{i}/dt = {ode}")
```

### Validation Methods

#### check_sink_sources()

Check for species that only appear as reactants (sinks) or products (sources).

**Parameters:**

- `errors` (bool): If True, raise exception on finding sinks/sources

**Description:**

Validates that species participate in both production and destruction reactions. Warns or errors if pure sinks or sources are found.

**Example:**

```python
net.check_sink_sources(errors=True)
```

#### check_recombinations()

Check for proper recombination reaction formatting.

**Parameters:**

- `errors` (bool): If True, raise exception on finding issues

**Description:**

Validates recombination reactions follow proper conventions.

#### check_isomers()

Check for isomer issues in the network.

**Parameters:**

- `errors` (bool): If True, raise exception on finding isomer issues

**Description:**

Identifies species with identical composition but different names.

#### check_unique_reactions()

Check that all reactions are unique (no duplicates).

**Parameters:**

- `errors` (bool): If True, raise exception on finding duplicates

**Description:**

Validates that the network doesn't contain duplicate reactions.

**Example:**

```python
# Run all validation checks
net.check_sink_sources(errors=False)
net.check_recombinations(errors=False)
net.check_isomers(errors=False)
net.check_unique_reactions(errors=False)
```

### Comparison Methods

#### `compare_reactions()`

Compare reactions between two networks.

**Parameters:**

- `other` (Network): Another network to compare with
- `verbosity` (int): Level of output detail (0=quiet, 1=normal, 2=verbose)

**Description:**

Compares reaction lists and identifies differences between networks.

**Example:**

```python
net1 = Network("networks/version1.dat")
net2 = Network("networks/version2.dat")
net1.compare_reactions(net2, verbosity=2)
```

#### `compare_species()`

Compare species lists between two networks.

**Parameters:**

- `other` (Network): Another network to compare with
- `verbosity` (int): Level of output detail

**Example:**

```python
net1.compare_species(net2, verbosity=1)
```

### Serialization Methods

#### to_jaff_file()

Save the network to a JAFF format file.

**Parameters:**

- `filename` (str): Output file path (will be gzip-compressed JSON)

**Description:**

Serializes the network to a compressed JSON format for fast loading.

**Example:**

```python
net.to_jaff_file("mynetwork.jaff")

# Load it back
net2 = Network("mynetwork.jaff")
```

## Supported File Formats

The Network class automatically detects and parses various file formats:

<!--### JAFF Format

Native JAFF format with simple reaction syntax:

```text
# Species are auto-detected from reactions
H + O -> OH, 1.2e-10 * (tgas/300)^0.5
H2 + O -> OH + H, 3.4e-11 * exp(-500/tgas)
```
-->

### KROME Format

KROME network files with `@format:` specification:

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate
1,H,O,,,OH,,,0,1e4,1.2e-10*(T/300)**0.5
```

### KIDA Format

Kinetic Database for Astrochemistry format:

```text
H + O -> OH : 1.2e-10 : 0.5 : 0.0
```

### UDFA Format

UMIST Database for Astrochemistry format with `:` separators.

### PRIZMO Format

PRIZMO format with variable definitions:

```text
VARIABLES{
    k1 = 1.2e-10
}

H + O -> OH, k1 * sqrt(tgas)
```

### UCL_CHEM Format

UCL_CHEM format with NAN placeholders.

## Matrix Properties

### Reactant Matrix (`rlist`)

A matrix of shape `(nreact, nspec)` where `rlist[i, j]` is the stoichiometric coefficient of species `j` as a reactant in reaction `i`.

```python
import numpy as np

# Check which species are reactants in reaction 0
reactants = net.rlist[0]
for i, coef in enumerate(reactants):
    if coef > 0:
        print(f"{net.species[i].name}: {coef}")
```

### Product Matrix (`plist`)

A matrix of shape `(nreact, nspec)` where `plist[i, j]` is the stoichiometric coefficient of species `j` as a product in reaction `i`.

```python
# Check products of reaction 0
products = net.plist[0]
for i, coef in enumerate(products):
    if coef > 0:
        print(f"{net.species[i].name}: {coef}")
```

## See Also

- [Species API](species.md) - Species class documentation
- [Reaction API](reaction.md) - Reaction class documentation
- [Elements API](elements.md) - Element analysis
- [Codegen API](codegen.md) - Code generation
- [File Parser API](file-parser.md) - Template processing

---

**Next**: Learn about [Species](species.md) with the Codegen class.
