---
tags:
    - Api
    - Elements
icon: lucide/atom
---

# Elements

The `elements` module provides utilities for extracting chemical elements from species and generating element-related matrices for conservation laws and stoichiometric analysis.

## Overview

The Elements class analyzes all species in a chemical reaction network to extract unique chemical elements and provides methods to generate matrices that describe element composition and presence across all species. These matrices are essential for:

- Checking element conservation in reactions
- Computing mass balance equations
- Analyzing stoichiometry
- Validating network consistency

## Module: `jaff.elements`

## Classes

### Elements

The main class for extracting and managing chemical elements from a reaction network.

#### Attributes

| Attribute  | Type        | Description                              |
| ---------- | ----------- | ---------------------------------------- |
| `net`      | Network     | The chemical reaction network to analyze |
| `elements` | list\[str\] | Sorted list of unique element symbols    |
| `nelems`   | int         | Total number of unique elements          |

#### Constructor

##### `__init__()`

Initialize the Elements analyzer for a given reaction network.

**Parameters**:

- `network` (Network): Chemical reaction network containing species to analyze

**Example**:

```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)
print(f"Found {elem.nelems} elements: {elem.elements}")
```

**Output**:

```
Found 3 elements: ['C', 'H', 'O']
```

#### Methods

##### `get_element_truth_matrix()`

Generate a binary matrix indicating element presence in each species.

Creates a matrix where entry `[i][j]` is `1` if element `i` is present in species `j`, and `0` otherwise. This is useful for checking element conservation laws and identifying species composition.

**Returns**:

- `list[list[int]]`: 2D matrix (nelems × nspecies) with binary values
    - `1` if the element is present in the species
    - `0` if the element is absent from the species

**Example**:

```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)
truth_matrix = elem.get_element_truth_matrix()

# Print which elements are in each species
for i, element in enumerate(elem.elements):
    print(f"{element}: {truth_matrix[i]}")
```

**Example Output**:

```
C: [1, 0, 1, 1, 0]  # C present in species 0, 2, 3
H: [0, 1, 0, 1, 1]  # H present in species 1, 3, 4
O: [1, 0, 1, 0, 1]  # O present in species 0, 2, 4
```

**Concrete Example**:

For elements `['C', 'H', 'O']` and species `['CO', 'H2', 'H2O', 'CH4']`:

```python
[
    [1, 0, 0, 1],   # C: present in CO and CH4
    [0, 1, 1, 1],   # H: present in H2, H2O, and CH4
    [1, 0, 1, 0]    # O: present in CO and H2O
]
```

##### `get_element_density_matrix()`

Generate a matrix showing element counts in each species.

Creates a matrix where entry `[i][j]` represents the number of atoms of element `i` present in species `j`. This is essential for stoichiometric calculations and mass balance equations.

**Returns**:

- `list[list[int]]`: 2D matrix (nelems × nspecies) with integer counts representing the number of atoms of each element in each species

**Example**:

```python
from jaff import Network
from jaff.elements import Elements

net = Network("networks/react_COthin")
elem = Elements(net)
density_matrix = elem.get_element_density_matrix()

# Print element counts for each species
for i, element in enumerate(elem.elements):
    print(f"{element}: {density_matrix[i]}")
```

**Example Output**:

```
C: [1, 0, 1, 1, 0]  # Number of C atoms in each species
H: [0, 2, 0, 4, 1]  # Number of H atoms in each species
O: [1, 0, 1, 0, 2]  # Number of O atoms in each species
```

**Concrete Example**:

For elements `['C', 'H', 'O']` and species `['CO', 'H2', 'H2O', 'CH4']`:

```python
[
    [1, 0, 0, 1],   # C: 1 in CO, 0 in H2, 0 in H2O, 1 in CH4
    [0, 2, 2, 4],   # H: 0 in CO, 2 in H2, 2 in H2O, 4 in CH4
    [1, 0, 1, 0]    # O: 1 in CO, 0 in H2, 1 in H2O, 0 in CH4
]
```

## See Also

- [Species API](species.md) - Individual species information
- [File Parser API](file-parser.md) - Using elements in templates
- [Network API](network.md) - Chemical network management
