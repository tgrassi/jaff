---
tags:
    - Api
icon: phosphor/atom
---

# jaff.physics

Jaff provides physical constants in four unit systems for astrochemical and physical calculations.

## Classes

| Class                             | Description                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------ |
| [`Constants`](constants/index.md) | Frozen dataclass of physical and astronomical constants in a given unit system |

## Available Instances

`jaff.physics.constants` exposes pre-built instances:

| Instance             | Unit System                              |
| -------------------- | ---------------------------------------- |
| `constants.cgs`      | CGS-ESU (cm, g, s, erg, esu)             |
| `constants.si`       | SI (m, kg, s, J, C)                      |
| `constants.gaussian` | Gaussian CGS (cm, g, s, erg, esu, Gauss) |
| `constants.natural`  | Natural units (ℏ = c = 1, energy in MeV) |

## Example

```python
from jaff.physics import constants

# CGS-ESU
c   = constants.cgs.c      # speed of light [cm/s]
k_b = constants.cgs.k_b    # Boltzmann constant [erg/K]

# SI
c_si = constants.si.c      # speed of light [m/s]

# Gaussian CGS
gyro = constants.gaussian.gyro_coeff  # [Hz/Gauss]

# Natural units (ℏ = c = 1, energies in MeV)
m_e = constants.natural.m_e  # electron mass [MeV]
```
