---
tags:
    - User-guide
    - Network
icon: lucide/sun
---

# Photochemistry

JAFF provides first-class support for photodissociation and photoionisation reactions. This page explains the physical model, how JAFF reads cross-section data, and how rate coefficients are derived from a discretised radiation field.

---

## Overview

A photochemical reaction has the form

$$
\text{Species} + h\nu \longrightarrow \text{Products}
$$

The reaction rate per unit volume is

$$
\mathcal{R} = n_\text{species} \int_0^\infty \sigma(E)\, c\, n_\gamma(E)\, dE
$$

where $\sigma(E)$ is the reaction cross section (cm²), $c$ is the speed of light (cm s⁻¹), and $n_\gamma(E)$ is the photon number density per unit energy (cm⁻³ erg⁻¹).

JAFF replaces the continuous integral with a sum over discrete **radiation frequency bands**:

$$
\mathcal{R} = n_\text{species} \sum_i k_i \cdot \rho_i
$$

where $\rho_i$ is the radiation energy or photon density in band $i$ and $k_i$ is a pre-computed rate coefficient for that band.

---

## Marking a Reaction as Photochemical

In the JAFF native `.jet` format, append `PHOTO` followed by the energy threshold (eV) instead of a rate expression:

```text
H -> H+ + E    []    PHOTO, 13.60
```

JAFF will look up the matching cross-section file in the Leiden database and integrate it over the configured radiation bands.

---

## Cross-Section Data — Leiden Database

JAFF ships with photoionisation and photodissociation cross sections from the **Leiden Observatory PDR database** (van Dishoeck et al.).

### File-naming convention

Cross-section files live in `src/jaff/data/xsecs/` and follow the pattern:

```text
Reactant1_Reactant2__Product1_Product2.dat
```

The double underscore `__` separates reactants from products. Species names are sorted alphabetically on each side.

### File format

The last `#`-prefixed comment line in each file is the column header. Two columns are required:

| Column name contains | Content |
| -------------------- | ------- |
| `wave`               | Wavelength in nanometres (nm) |
| `ion` **or** `dis`   | Cross section in cm² (selection depends on the reaction's charge balance) |

### Energy conversion

Wavelengths are converted to photon energies in erg:

$$
E \;[\text{erg}] = \frac{h \cdot c}{\lambda \;[\text{nm}] \times 10^{-7}}
$$

---

## Radiation Field Discretisation

The radiation field is divided into contiguous energy bands. You specify the band boundaries in `jaff.toml` (see [Configuration File](../code-generation/jaff-toml.md)):

```toml
[radiation]
bands             = [13.6, "inf"]   # band edges in eV; "inf" for open upper bound
power_law_index   = 0               # photon-number spectrum index α
energy_density    = false           # use photon density (false) or energy density (true)
rsl               = 2.99792458e10   # speed of light (cm/s)
```

### Photon spectrum

The photon number density spectrum is assumed to be a power law in photon energy:

$$
n(E) \propto E^{\alpha - 2}
$$

where $\alpha$ is `power_law_index`. Setting $\alpha = 0$ gives $n(E) \propto E^{-2}$, i.e. equal energy per logarithmic interval.

### Band-averaged cross section

For band $i$ spanning $[E_\text{lo}, E_\text{hi}]$:

$$
\langle\sigma\rangle_i = \frac{\displaystyle\int_{E_\text{lo}}^{E_\text{hi}} \sigma(E)\, n(E)\, dE}{\displaystyle\int_{E_\text{lo}}^{E_\text{hi}} n(E)\, dE}
$$

### Rate coefficient

In **photon-density mode** (`energy_density = false`):

$$
k_i = c \cdot \langle\sigma\rangle_i
$$

In **energy-density mode** (`energy_density = true`):

$$
k_i = \frac{c \cdot \langle\sigma\rangle_i}{\langle E\rangle_i}
$$

where $\langle E\rangle_i$ is the photon-number–weighted average energy in the band.

---

## Generated Rate Expressions

After band integration, each photochemical reaction contributes one term per band to the ODE right-hand side:

$$
\frac{d[\text{Species}]}{dt} \supset -n_\text{species} \sum_i k_i \cdot \rho_i
$$

The generated code uses the radiation density array `den[i]` as the runtime variable for $\rho_i$. The ODE for the radiation field itself can be obtained from `#!python Network.sradodes()`.

---

## Python API

```python
from jaff import Network

# Enable photochemistry by declaring radiation bands
net = Network(
    "networks/h_photoionization/h_photo.jet",
    rad_bands=[13.6, float("inf")],   # band edges in eV
    rad_powerlaw_index=0,
    rad_energy_density=False,
)

# Inspect photochemical reactions
photo = net.reactions.photo_reactions()
for rxn in photo:
    print(rxn.verbatim)

# Symbolic radiation ODEs
print(net.sradodes())
```

<!-- prettier-ignore -->
!!! note "Threshold energy"
    The `PHOTO, <eV>` threshold in the `.jet` file is used to select which cross-section file to load and which band edges apply to this reaction. Reactions whose threshold lies above the upper edge of a band are not assigned a rate coefficient for that band.
