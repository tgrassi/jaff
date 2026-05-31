---
tags:
    - Api
---

# Constants

`jaff.physics.constants.Constants`

Frozen dataclass holding physical and astronomical constants in a consistent unit system. All values follow CODATA 2018 recommended values where applicable.

Four pre-built instances are available: `constants.cgs` (CGS-ESU), `constants.si` (SI), `constants.gaussian` (Gaussian CGS), and `constants.natural` (natural units, ℏ = c = 1).

## Constructor

`#!python Constants(c, h, h_bar, G, k_b, e, m_e, m_p, m_n, amu, me_mp, m_sun, r_sun, l_sun, pc, kpc, mpc, au, ly, H0, sigma_sb, a_rad, alpha, sigma_T, lambda_C, a0, Ry_hc, Ry, r_e, gyro_coeff, ev_to_erg, mu_H, mu_H2, kb_ev, T_cmb, T_1ev, nH_ref)`

All fields are required. The instance is frozen (immutable) after creation.

## Attributes

**Fundamental constants**

| Attribute | Type | Description |
|-----------|------|-------------|
| `c` | `float` | Speed of light |
| `h` | `float` | Planck constant |
| `h_bar` | `float` | Reduced Planck constant |
| `G` | `float` | Gravitational constant |
| `k_b` | `float` | Boltzmann constant |
| `e` | `float` | Elementary charge |
| `m_e` | `float` | Electron mass |
| `m_p` | `float` | Proton mass |
| `m_n` | `float` | Neutron mass |
| `amu` | `float` | Atomic mass unit |
| `me_mp` | `float` | Electron-to-proton mass ratio |

**Astronomical constants**

| Attribute | Type | Description |
|-----------|------|-------------|
| `m_sun` | `float` | Solar mass |
| `r_sun` | `float` | Solar radius |
| `l_sun` | `float` | Solar luminosity |
| `pc` | `float` | Parsec |
| `kpc` | `float` | Kiloparsec |
| `mpc` | `float` | Megaparsec |
| `au` | `float` | Astronomical unit |
| `ly` | `float` | Light year |
| `H0` | `float` | Hubble constant |

**Radiation and electromagnetism**

| Attribute | Type | Description |
|-----------|------|-------------|
| `sigma_sb` | `float` | Stefan-Boltzmann constant |
| `a_rad` | `float` | Radiation constant (a = 4σ/c) |
| `alpha` | `float` | Fine-structure constant (dimensionless, ≈ 1/137) |
| `sigma_T` | `float` | Thomson scattering cross section |
| `lambda_C` | `float` | Compton wavelength of the electron |
| `a0` | `float` | Bohr radius |
| `Ry_hc` | `float` | Rydberg energy in the unit system's energy units |
| `Ry` | `float` | Rydberg energy in eV (always 13.605693 eV) |

**Gas/plasma astrophysics**

| Attribute | Type | Description |
|-----------|------|-------------|
| `r_e` | `float` | Classical electron radius |
| `gyro_coeff` | `float` | Gyration-frequency coefficient (charge/mass or equivalent) |

**Astrochemistry**

| Attribute | Type | Description |
|-----------|------|-------------|
| `ev_to_erg` | `float` | 1 eV expressed in the unit system's energy unit |
| `mu_H` | `float` | Mean mass of a hydrogen atom |
| `mu_H2` | `float` | Mean mass of a hydrogen molecule |
| `kb_ev` | `float` | Boltzmann constant in eV/K |
| `T_cmb` | `float` | CMB temperature in Kelvin (2.725 K) |
| `T_1ev` | `float` | Temperature equivalent of 1 eV |
| `nH_ref` | `float` | Reference hydrogen number density (1 H atom per unit volume) |

**Cross sections**

| Attribute | Type | Description |
|-----------|------|-------------|
| `barn` | `float` | 1 barn in the unit system's area unit |
| `mbarn` | `float` | 1 megabarn in the unit system's area unit |

**Reference**

| Attribute | Type | Description |
|-----------|------|-------------|
| `n_A` | `float` | Avogadro constant (dimensionless) |
| `R_gas` | `float` | Molar gas constant (k_b × N_A) |
