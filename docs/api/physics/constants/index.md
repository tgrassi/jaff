---
tags:
    - Api
---

# Constants

`jaff.physics.constants.Constants`

Frozen dataclass holding physical and astronomical constants in a consistent unit system.

Two pre-built instances are available: `constants.cgs` (CGS) and `constants.si` (SI).

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
| `a_rad` | `float` | Radiation constant |
| `alpha` | `float` | Fine structure constant |
| `sigma_T` | `float` | Thomson cross section |
| `lambda_C` | `float` | Compton wavelength |
| `a0` | `float` | Bohr radius |
| `Ry_hc` | `float` | Rydberg constant × hc |
| `Ry` | `float` | Rydberg energy |
| `r_e` | `float` | Classical electron radius |
| `gyro_coeff` | `float` | Cyclotron frequency coefficient |

**Astrochemistry**

| Attribute | Type | Description |
|-----------|------|-------------|
| `ev_to_erg` | `float` | eV to erg conversion |
| `mu_H` | `float` | Mean molecular weight of atomic hydrogen |
| `mu_H2` | `float` | Mean molecular weight of H2 |
| `kb_ev` | `float` | Boltzmann constant in eV/K |
| `T_cmb` | `float` | CMB temperature |
| `T_1ev` | `float` | Temperature corresponding to 1 eV |
| `nH_ref` | `float` | Reference hydrogen number density |
