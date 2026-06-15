---
tags:
    - Api
---

# Constants

`jaff.physics.constants`

Physical and astronomical constants exposed as module-level
[`astropy.units.Quantity`](https://docs.astropy.org/en/stable/units/quantity.html)
objects. Each constant carries both a value and a unit, sourced from
[`astropy.constants`](https://docs.astropy.org/en/stable/constants/index.html)
(CODATA 2018) where available, and computed from those primitives otherwise.
Constant names follow the `astropy.constants` spelling (`k_B`, `m_p`, `M_sun`,
`N_A`, `u`, `R`, ...).

## Unit systems

There are no longer separate `cgs` / `si` / `gaussian` / `natural` tables.
Because every constant is a unit-aware `Quantity`, the unit system is selected
**per quantity** at the call site:

```python
from jaff.physics import constants as c

c.c.cgs            # speed of light in CGS -> <Quantity 2.99792458e+10 cm / s>
c.c.si             # ... in SI             -> <Quantity 2.99792458e+08 m / s>
c.k_B.to("eV / K") # ... in any unit       -> <Quantity 8.617e-05 eV / K>
float(c.m_p.cgs.value)  # bare float (grams) when a number is required
```

The elementary charge keeps astropy's electromagnetic-unit views:

```python
c.e.esu   # Gaussian / CGS-ESU (Franklin) -> <Quantity 4.803e-10 Fr>
c.e.si    # SI (Coulomb)                   -> <Quantity 1.602e-19 C>
```

!!! note "Migration from the old `Constants` dataclass"
| Old | New |
|-----|-----|
| `constants.cgs.c` | `constants.c.cgs` |
| `constants.cgs.k_b` | `constants.k_B.cgs` |
| `constants.si.m_e` | `constants.m_e.si` |
| `constants.cgs.ev_to_erg` | `(1 * u.eV).to("erg")` |
| `constants.cgs.kb_ev` | `constants.k_B.to("eV / K")` |

    The `gaussian` and `natural` systems and the trivial conversion factors
    (`ev_to_erg`, `kb_ev`, `Ry_hc`) have been removed; derive them on demand
    with `.to(...)`.

## Constants

**Fundamental constants**

| Name    | Description                                   |
| ------- | --------------------------------------------- |
| `c`     | Speed of light in vacuum                      |
| `h`     | Planck constant                               |
| `hbar`  | Reduced Planck constant (h / 2π)              |
| `G`     | Newtonian gravitational constant              |
| `k_B`   | Boltzmann constant                            |
| `e`     | Elementary charge (use `.esu` or `.si`)       |
| `m_e`   | Electron rest mass                            |
| `m_p`   | Proton rest mass                              |
| `m_n`   | Neutron rest mass                             |
| `u`     | Atomic mass unit (1 u)                        |
| `me_mp` | Electron-to-proton mass ratio (dimensionless) |

**Astronomical constants**

| Name    | Description                     |
| ------- | ------------------------------- |
| `M_sun` | Solar mass                      |
| `R_sun` | Solar radius                    |
| `L_sun` | Solar luminosity                |
| `pc`    | Parsec                          |
| `kpc`   | Kiloparsec                      |
| `Mpc`   | Megaparsec                      |
| `au`    | Astronomical unit               |
| `ly`    | Light-year                      |
| `H0`    | Hubble constant (67.4 km/s/Mpc) |

**Radiation and electromagnetism**

| Name       | Description                                      |
| ---------- | ------------------------------------------------ |
| `sigma_sb` | Stefan-Boltzmann constant                        |
| `a_rad`    | Radiation constant (a = 4σ/c)                    |
| `alpha`    | Fine-structure constant (dimensionless, ≈ 1/137) |
| `sigma_T`  | Thomson scattering cross section                 |
| `lambda_C` | Compton wavelength of the electron               |
| `a0`       | Bohr radius                                      |
| `Ry`       | Rydberg energy (≈ 13.6 eV)                       |

**Gas/plasma astrophysics**

| Name         | Description                                                   |
| ------------ | ------------------------------------------------------------- |
| `r_e`        | Classical electron radius (α² · a0)                           |
| `gyro_coeff` | Electron gyromagnetic coefficient (e / m_e) in CGS-ESU (Fr/g) |

**Astrochemistry**

| Name     | Description                                          |
| -------- | ---------------------------------------------------- |
| `mu_H`   | Mean mass of a hydrogen atom (≈ proton mass)         |
| `mu_H2`  | Mean mass of a hydrogen molecule (≈ 2 proton masses) |
| `nH_ref` | Reference hydrogen number per unit mass (1 / m_p)    |
| `T_cmb`  | CMB temperature (2.725 K)                            |
| `T_1ev`  | Temperature equivalent of 1 eV                       |

**Cross sections**

| Name    | Description           |
| ------- | --------------------- |
| `barn`  | 1 barn (1e-24 cm²)    |
| `mbarn` | 1 megabarn (1e6 barn) |

**Reference**

| Name  | Description                    |
| ----- | ------------------------------ |
| `N_A` | Avogadro constant              |
| `R`   | Molar gas constant (k_B × N_A) |
