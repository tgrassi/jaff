---
tags:
    - Api
    - Species
icon: lucide/hexagon
---

# Species

## Overview

The `Species` class represents a unique chemical entity (atom, molecule, ion, or grain) within a JAFF reaction network. It handles the parsing of chemical formulas to determine atomic composition, mass calculation, charge determination, and formatting for LaTeX and code generation.

```python
from jaff import Species

# Define atomic masses
mass_dict = {"H": {"mass": 1.00784, "name": "Hydrogen"}, "O": {"mass": 15.999, "name": "Oxygen"}}

# Create a water molecule species
water = Species(name="H2O", mass_dict=mass_dict, index=5)

print(f"Name: {water.name}")        # "H2O"
print(f"Mass: {water.mass}")        # 18.01468
print(f"Charge: {water.charge}")    # 0
print(f"LaTeX: {water.latex}")      # "{\rm H_{2}O}"
```

## Class Definition

```python
class Species:
    def __init__(self, name, mass_dict, index):
        """
        Initialize a chemical species.

        Args:
            name (str): The name of the species (e.g., "H2O", "HCO+").
            mass_dict (dict): Dictionary mapping atom names to their masses.
            index (int): Unique integer identifier for this species in the network.

        Raises:
            SystemExit: If an invalid name for electrons is used (e.g., "eletron", "E").
                       Use "e-" for electrons.
        """
```

## Attributes

| Attribute    | Type      | Description                                       |
| ------------ | --------- | ------------------------------------------------- |
| `name`       | str       | The raw name of the species (e.g., "HCO+")        |
| `index`      | int       | The unique network index assigned to this species |
| `mass`       | float     | Total mass calculated from atomic composition     |
| `charge`     | int       | Electrical charge (e.g., +1, 0, -1)               |
| `exploded`   | list[str] | List of atoms constituting the species            |
| `latex`      | str       | LaTeX formatted string for display                |
| `fidx`       | str       | Variable name for code generation (e.g., "idx_h") |
| `serialized` | str       | Canonical string representation of composition    |

## String Representations

### `__str__()`

Returns the species name.

```python
s = Species("H2O", mass_dict, 0)
print(str(s))  # "H2O"
```

### `__repr__()`

Returns a detailed string representation for debugging.

```python
s = Species("H2O", mass_dict, 0)
print(repr(s))
# Species(name='H2O', mass=18.015, index=0)
```

## Code Generation Helpers

### `get_fidx()`

Generates a sanitized variable name used for indexing in generated C/Fortran code.

```python
variable = s.get_fidx()
```

**Naming Rules:**

- **"e-"**: Returns `"idx_e"`
- **General**: Returns `"idx_"` + name in lowercase.
- **Special Characters**:
    - `+` becomes `j`
    - `-` becomes `k`
- **Example**: "HCO+" $\to$ `"idx_hcoj"`

## Core Methods

### `parse()`

Parses the species name to determine its properties. This is called automatically during initialization.

```python
s.parse(mass_dict)
```

**Functionality:**

1.  **Composition**: Deconstructs the chemical formula (e.g., "H2O") into a list of atoms (`["H", "H", "O"]`) using the provided `mass_dict` keys.
2.  **Mass**: Sums the masses of constituent atoms.
3.  **Charge**:
    - "e-" is assigned charge -1.
    - Scans the _end_ of the string for `+` or `-` characters to determine ion charge.
4.  **LaTeX**: Generates a formatted string for equations.
    - Subscripts numbers (H2 $\to$ H$_{2}$)
    - Formats charge (+ $\to$ $^{+}$)
    - Converts special tags:
        - `_ORTHO` $\to$ prefix `o`
        - `_PARA` $\to$ prefix `p`
        - `_META` $\to$ prefix `m`
        - `_DUST` $\to$ suffix `ice`
        - `GRAIN` $\to$ `g`

### `serialize()`

Generates a canonical string representation of the species based on its atomic composition.

```python
canonical = s.serialize()
```

**Logic:**

- Takes the `exploded` atomic list.
- Sorts the atoms alphabetically.
- Joins them with forward slashes `/`.
- **Example**: "H2O" becomes `"H/H/O"`.
- Used internally to compare species identity regardless of isomer naming.

## See Also

- [Network API](network.md) - Container that manages lists of Species.
- [Reaction API](reaction.md) - Reactions involving these Species.
