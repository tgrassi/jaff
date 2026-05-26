---
tags:
    - Api
icon: lucide/atom
---

# jaff.physics

Physical constants and unit systems for astrochemical calculations.

## Classes

| Class | Description |
|-------|-------------|
| [`Constants`](constants.md) | Frozen dataclass of physical and astronomical constants in a given unit system |

## Available Instances

`jaff.physics.constants` exposes pre-built instances:

| Instance | Unit System |
|----------|-------------|
| `constants.cgs` | CGS (cm, g, s) |
| `constants.si` | SI (m, kg, s) |

## Quick Start

```python
from jaff.physics import constants

# CGS constants
c   = constants.cgs.c      # speed of light [cm/s]
k_b = constants.cgs.k_b    # Boltzmann constant [erg/K]

# SI constants
c_si = constants.si.c      # speed of light [m/s]
```
