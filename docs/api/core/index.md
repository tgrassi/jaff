---
tags:
    - Api
    - Network
icon: phosphor/git-diff
---

# jaff.core

The `jaff.core` subpackage contains the primary data-model classes for loading, parsing, and representing chemical reaction networks.

## Classes

| Class                              | Description                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------- |
| [`Network`](network/index.md)      | Load and manage a chemical reaction network from file                                 |
| [`Species`](species/index.md)      | Typed collection of `Specie` objects within a network, network or reaction            |
| [`Specie`](specie/index.md)        | Single chemical species with mass, charge, and other attributes and helper methods    |
| [`Reactions`](reactions/index.md)  | Typed collection of `Reaction` objects within a network                               |
| [`Reaction`](reaction/index.md)    | Single chemical reaction with rate expression and other attributes and helper methods |
| [`Elements`](elements/index.md)    | Extract elements from species and and their collective properties                     |
| [`Element`](element/index.md)      | Single chemical element with atomic properties                                        |

## Quick Start

```python
from jaff import Network
from jaff.core import Elements

net = Network("networks/COthin/react_COthin")

# Access species and reactions
print(f"Species: {net.species.count}")
print(f"Reactions: {net.reactions.count}")

# Element analysis
elem = Elements(net)
print(f"Elements: {net.elements.symbols}")
```
