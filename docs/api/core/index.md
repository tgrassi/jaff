---
tags:
    - Api
    - Network
icon: lucide/git-compare-arrows
---

# jaff.core

The core classes focus on loading, parsing, and representing chemical reaction networks.

## Classes

| Class                              | Description                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------- |
| [`Network`](network.md)            | Load and manage a chemical reaction network from file                                 |
| [`Species`](species.md)            | Typed collection of `Specie` objects within a network, network or reaction            |
| [`Specie`](species.md#specie)      | Single chemical species with mass, charge, and other attributes and helper methods    |
| [`Reactions`](reaction.md)         | Typed collection of `Reaction` objects within a network                               |
| [`Reaction`](reaction.md#reaction) | Single chemical reaction with rate expression and other attributes and helper methods |
| [`Elements`](elements.md)          | Extract elements from species and and their collective properties                     |
| [`Element`](elements.md#element)   | Single chemical element with atomic properties                                        |

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
