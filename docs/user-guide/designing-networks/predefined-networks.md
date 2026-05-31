---
tags:
    - User-guide
    - Network
---

# Predefined Networks

JAFF ships a set of ready-to-use reaction networks in the `networks/` directory. They cover a range of physical regimes and serve as both already verified research networks and format demonstrations.

## Overview

| Network                                   | Format      | Reactions | Description                               |
| ----------------------------------------- | ----------- | --------- | ----------------------------------------- |
| [`h_photoionization`](#h_photoionization) | JAFF native | 2         | Minimal hydrogen photoionisation          |
| [`demos`](#demos)                         | Mixed       | —         | Format demonstrations                     |
| [`GOW`](#gow)                             | KIDA        | ~50       | Gong, Ostriker & Wolfire (2017)           |
| [`COthin`](#cothin)                       | KROME       | ~287      | CO chemistry (Glover+2010)                |
| [`popsicle_semenov`](#popsicle_semenov)   | KROME       | ~116      | Primordial + metal chemistry for POPSICLE |
| [`uclchem_small_gas`](#uclchem_small_gas) | UCLCHEM     | ~563      | Small gas-phase network from UCLCHEM      |
| [`kida_uva_2024`](#kida_uva_2024)         | KIDA        | ~8 275    | Full KIDA UVA 2024 gas-phase database     |
| [`rate22_final`](#rate22_final)           | UDFA        | ~8 767    | Full UMIST Rate22 database                |

---

## h_photoionization

**File:** `networks/h_photoionization/h_photo.jet`

A two-reaction JAFF native network illustrating the photochemistry pipeline. It contains one photoionisation reaction with a 13.6 eV threshold and one radiative recombination reaction, making it the smallest self-contained network for testing photochemistry.

```text
H -> H+ + E          []         PHOTO, 13.60
H+ + E -> H          []         2.63e-13*(Tgas/1e4)**(-0.7)
```

---

## demos

**Files:** `networks/demos/demo1.jet`, `networks/demos/demo2.jet`

Demonstration files, not intended for scientific use.

- **`demo1.jet`** — A mixed-format file containing reactions written in PRIZMO, KIDA, UDFA, and KROME syntax side-by-side. Useful for checking format auto-detection and as a format cheat-sheet.
- **`demo2.jet`** — A two-reaction JAFF native snippet used in the documentation examples.

---

## GOW

**File:** `networks/GOW/GOW.jet`

The Gong, Ostriker & Wolfire (2017) diffuse-ISM chemistry network in KIDA format. It covers hydrogen, carbon, and oxygen chemistry relevant to the cold neutral medium and was originally distributed with the [Athena++](https://www.athena-astro.app/) code.

**Reference:** [Gong, Ostriker & Wolfire, ApJ 843, 38 (2017)](https://doi.org/10.3847/1538-4357/aa7561)

The GOW directory ships three files:

```text
GOW/
├── GOW.jet      reaction network (KIDA format)
├── GOW.jfunc    custom rate and heating/cooling function definitions
└── GOW.hdf5     interpolation tables consumed by those functions
```

### `GOW.hdf5` data tables

`GOW.jfunc` defines several heating/cooling functions that are not closed-form —
they call interpolation functions whose grids live in `GOW.hdf5`. The file is
organised into three top-level groups, one per physical process. All datasets
are stored in log-scaled form following the Omukai+2010 / Gong+2017 fits.

```text
GOW.hdf5
├── co/                  CO rotational-line cooling — feeds cooling_CO()
│   ├── TCO       (11,)  int64    gas-temperature grid axis [K], 10 → 2000
│   ├── NeffCO    (11,)  float64  log₁₀ LVG column parameter Ñ axis
│   │                             [cm⁻²/(km s⁻¹)], 14 → 19
│   ├── L0CO      (11,)  float64  optically-thin cooling coeff L₀, 1-D over TCO
│   ├── LLTECO    (121,) float64  LTE cooling coeff L_LTE, 2-D (TCO × NeffCO)
│   ├── nhalfCO   (121,) float64  half-cooling density n₁⁄₂, 2-D (TCO × NeffCO)
│   └── alphaCO   (121,) float64  fit exponent α (dimensionless), 2-D
│       └─ group attr  nd_order = ['TCO', 'NeffCO']   ← axis order of 2-D tables
│
├── dust/                gas–dust collisional cooling Ψ_GD — feeds cooling_dust_coll()
│   ├── lognH     (150,) float64  log₁₀ H-nucleus density [cm⁻³], 0 → 6
│   ├── logTg     (150,) float64  log₁₀ gas temperature [K], 0.5 → 4
│   └── logps     (150,) float64  log₁₀ Ψ_GD cooling-rate coeff at (lognH, logTg)
│
└── radiative_cooling/   radiative cooling vs. radiation temperature
    ├── log_Trad       (110,) float64  log₁₀ radiation temperature [K], 3.8 → 8.16
    ├── log_gamma_H_He (110,) float64  log₁₀ H+He cooling coeff over log_Trad
    └── log_gamma_Z    (110,) float64  log₁₀ metal (Z) cooling coeff over log_Trad
```

- **`co/`** — the four datasets `L0CO`, `LLTECO`, `nhalfCO`, `alphaCO` are the
  pieces of the Neufeld-style CO cooling fit, looked up by `L0_CO_interp1d`,
  `LLTE_CO_interp2d`, `nHalf_CO_interp2d`, and `alpha_CO_interp2d` against the
  `TCO` (temperature) and `NeffCO` (LVG column) axes. The 121-element tables are
  the `11 × 11` grids flattened in the order given by the `nd_order` attribute.
- **`dust/`** — `(lognH, logTg)` form a `15 × 10` grid; `logps` is the tabulated
  Ψ_GD value at each node, used by `PsiGD_coll_interp2d` to set the dust
  temperature implicitly in the gas–dust collisional cooling term.
- **`radiative_cooling/`** — radiative cooling coefficients for the H+He and
  metal (`Z`) components as a function of radiation temperature, indexed by
  `log_Trad`.

---

## COthin

**File:** `networks/COthin/react_COthin.jet`

A CO-chemistry network in KROME format based on Glover+2010 and additional literature sources. It is designed for optically thin environments and is well-suited for simulations of diffuse molecular clouds where CO formation and destruction rates are needed without full grain-surface chemistry.

**Reference:** [Glover et al., MNRAS 404, 2 (2010)](https://doi.org/10.1111/j.1365-2966.2009.15718.x)

---

## popsicle_semenov

**File:** `networks/popsicle_semenov/react_popsicle_semenov.jet`

A KROME-format network built for the POPSICLE simulation code (Sharda & Menon 2024). It combines a primordial chemistry network (including deuterium species) with metal-line cooling reactions from Omukai (2000), Omukai+2005, Glover & Jappsen (2007), and Glover+2010. Dust opacity follows Semenov+2003. Cosmic-ray and photochemistry reactions are not included.

**Reference:** [Sharda & Menon (2024)](https://academic.oup.com/mnras/article/540/2/1745/8133918)

---

## uclchem_small_gas

**File:** `networks/uclchem_small_gas/uclchem_small_gas_network.jet`

A small gas-phase development network generated by UCLCHEM v3.5.1. It includes a minimal set of ice-surface species alongside UMIST Rate22 gas-phase reactions. The network uses the UCLCHEM species notation: `@` for bulk ice, `#` for surface ice, and no prefix for gas phase.

<!-- prettier-ignore -->
!!! warning
    This network has not been validated for scientific use. It is provided for development and testing purposes only.

**Generated by:** [Gijs Vermariën](https://vermarien.com/) using UCLCHEM v3.5.1

---

## kida_uva_2024

**File:** `networks/kida_uva_2024/gas_reactions_kida.uva.2024.jet`

The complete KIDA UVA 2024 gas-phase reaction database in KIDA format. It covers a broad range of ion-neutral, neutral-neutral, photodissociation, and cosmic-ray reactions and is one of the primary reference databases in astrochemical modelling.

**Reference:** [Wakelam et al., A&A 689, A63 (2024)](https://doi.org/10.1051/0004-6361/202450606)

**Source:** [kida.astrochem-tools.org](https://kida.astrochem-tools.org/)

---

## rate22_final

**File:** `networks/rate22_final/rate22_final.rates.jet`

The complete UMIST Database for Astrochemistry Rate22 release in UDFA format. It is the largest network included and covers gas-phase reactions for over 500 species across a wide temperature range.

**Reference:** [Millar et al., A&A 682, A109 (2024)](https://doi.org/10.1051/0004-6361/202346908)

**Source:** [umistdatabase.uk](https://umistdatabase.uk/)
