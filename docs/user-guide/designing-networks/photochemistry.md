---
tags:
    - User-guide
    - Network
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
\mathcal{R} = \prod_i {n_i}^{\alpha} \int_0^\infty \sigma(E_\nu)\, c\, \dfrac{ \partial n_\gamma}{\partial E_\nu}\, dE_{\nu}
$$

where $\sigma(E_\nu)$ is the reaction cross section ($\text{cm}^2$), $c$ is the speed of light ($\text{cm s}^{-1}$), and $n_\gamma$ is the photon number density ($\text{cm}^{-3}$). The subscript $\gamma$ signifies the local radiation field and a subscript of $\nu$ signifies the frequency of the photon. JAFF uses high-resolution cross-section tables from the [Leiden Observatory Database](https://home.strw.leidenuniv.nl/~ewine/photo/index.html) and the [NORAD Database](https://norad.astronomy.osu.edu/) for photo-dissociaton and photo-ionization reactions respectively to store and calculate band averaged cross-sections.

When the radiation energy density per band is calculated, JAFF replaces the continuous integral with a sum over discrete **radiation frequency bands**:

$$
\mathcal{R} = \prod_i {n_i}^{\alpha} \sum_i k_i \cdot \rho_i
$$

where $\rho_i$ is the radiation energy or photon density in band $i$ and $k_i$ is a pre-computed rate coefficient for that band.

<!-- prettier-ignore -->
!!! tip "Radiation source terms"
    If a reaction adds photons to the local radiation field, it can be specified using a custom `deltaRad<N>` function. Details are mentioned in [Auxiliary functions file](auxiliary-functions.md)

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

where $\alpha$ is `power_law_index`. Setting $\alpha = 0$ gives $n(E) \propto E^{-2}$, i.e. equal energy per logarithmic bin which is the default assumption.

### Band-averaged cross section

For band $i$ spanning $[E_\text{lo}, E_\text{hi}]$:

$$
\langle\sigma\rangle_i = \frac{\displaystyle\int_{E_\text{lo}}^{E_\text{hi}} \sigma(E_\nu)\, \dfrac{ \partial n_\gamma}{\partial E_\nu}\, dE_\nu}{\displaystyle\int_{E_\text{lo}}^{E_\text{hi}} \dfrac{ \partial n_\gamma}{\partial E_\nu}\, dE_\nu}
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
\frac{dn_i}{dt} \supset -\prod_i {n_i}^{\alpha} \sum_i k_i \cdot \rho_i
$$

The generated code uses the radiation density array `den[i]` as the runtime variable for $\rho_i$. The ODE for the radiation field itself can be obtained from `#!python Network.sradodes()`.

---

## Marking a Reaction as Photochemical

In the `PRIZMO` format, append `PHOTO` followed by the energy threshold (eV) instead of a rate expression:

```text
H -> H+ + E    []    PHOTO, 13.60
```

JAFF will look up the matching cross section in its bundled database and integrate it over the configured radiation bands.

---

## Cross-Section Data

JAFF bundles cross sections from three sources. At network-load time the
serialized reaction key (`Reactant1_Reactant2__Product1_Product2`, the
[serialized form of the reaction](../../api/core/reaction/index.md)) is looked
up in `jaff.db`, and the cross-section arrays are attached to the reaction's
[`xsecs_dict`](../working-with-networks/reactions.md).

| Source                                                                                         | Processes                                           | Notes                        |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------- | ---------------------------- |
| **Leiden** PDR database ([van Dishoeck et al.](https://home.strw.leidenuniv.nl/~ewine/photo/)) | photoabsorption, photodissociation, photoionization | Tabulated cross sections     |
| **NORAD** / OP ([Nahar, OSU](https://norad.astronomy.osu.edu/))                                | photoionization (ground state)                      | Tabulated, per ion Z = 1..26 |
| **Verner et al. 1996** ([ADS](https://ui.adsabs.harvard.edu/abs/1996ApJ...465..487V/abstract)) | photoionization                                     | Analytic fits σ(E)           |

### Storage layout

Tabulated cross sections ship as two collapsed HDF5 files, one group per
serialized reaction, all datasets co-sorted by ascending photon energy:

```text
src/jaff/data/xsecs/leiden/leiden.hdf5   # one group per reaction (abs/diss/ion)
src/jaff/data/xsecs/norad/norad.hdf5     # one group per reaction (ionization)
src/jaff/data/xsecs/verner/verner_1996.csv   # analytic-fit parameters
```

`photon_energy` is stored in **eV** and every cross-section dataset
(`photoabsorption` / `photodissociation` / `photoionization`) in **cm²**.

These assets feed two SQLite tables in `jaff.db`, which is what JAFF actually
queries at runtime (see [Codebase Structure](../../development/codebase-structure.md)):

- `photo_reaction_cross_sections` — one row per reaction, with `pa`/`pi`/`pd`
  process flags and a `file.hdf5::<group>` pointer into the Leiden or NORAD
  HDF5 file.
- `verner_cross_sections` — the Verner analytic σ(E) expression as a
  SymPy-parseable string (symbol `E`, photon energy in erg, σ in cm²).

### What lands on the reaction

For tabulated sources, `reaction.xsecs_dict` is an `XsecsProps` dict carrying
the `photon_energy` grid (eV) plus any of `photo_absorption`,
`photo_dissociation`, `photo_ionization` (cm² arrays, or `None`). The radiation
integrator reads these arrays directly and integrates them numerically over
each band; for photoionization it falls back to the Verner analytic fit when no
tabulated entry exists.

<!-- prettier-ignore -->
!!! note "Threshold energy"
    The `PHOTO, <eV>` threshold in the network file selects which band edges
    apply to a reaction. Reactions whose threshold lies above the upper edge of
    a band are not assigned a rate coefficient for that band.

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

# Cross sections are attached at load time
rxn = photo[0]
rxn.xsecs_dict["photon_energy"]     # eV grid
rxn.xsecs_dict["photo_ionization"]  # cm² array (or None)
rxn.plot_xsecs()                    # visualise σ(E)

# Symbolic radiation ODEs
print(net.sradodes())
```

Cross-section lookup is also exposed directly via `jaff.physics.photochemistry`:

```python
from jaff.physics import photochemistry

photochemistry.get_xsec(rxn)         # XsecsProps from the tabulated databases
photochemistry.get_verner_xsec(rxn)  # analytic Verner σ(E) (sympy) or None
```
