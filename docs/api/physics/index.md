---
tags:
    - Api
icon: phosphor/atom
---

# jaff.physics

Physical constants and photochemical cross-section lookup for astrochemical calculations.

## Classes

| Class                             | Description                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------ |
| [`Constants`](constants/index.md) | Frozen dataclass of physical and astronomical constants in a given unit system |
| `Photochemistry`                  | Photo cross-section lookup from the bundled databases (see below)               |

## Submodules

| Submodule                            | Description                                                                  |
| ------------------------------------ | ---------------------------------------------------------------------------- |
| `constants`                          | Pre-built physical-constant instances (see below)                            |

## Photochemistry methods

`jaff.physics.Photochemistry` resolves a reaction's cross sections from `jaff.db`.
Constructing it downloads the cross-section data files on first use (cached
thereafter), so instantiate once and reuse:

```python
from jaff.physics import Photochemistry

photo = Photochemistry()
photo.get_xsec(rxn)         # XsecsProps from the tabulated databases
photo.get_verner_xsec(rxn)  # analytic Verner σ(E) (sympy) or None
```

| Method                         | Returns                  | Description                                                       |
| ------------------------------ | ------------------------ | ----------------------------------------------------------------- |
| `get_xsec(reaction)`           | `XsecsProps or None`     | Tabulated cross sections (Leiden / NORAD): `photon_energy` (eV) plus `photo_absorption`/`photo_ionization`/`photo_dissociation` (cm²) |
| `get_verner_xsec(reaction)`    | `sympy.Basic or None`    | Analytic Verner (1996) σ(E) expression (symbol `E` in erg, σ in cm²) |

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
