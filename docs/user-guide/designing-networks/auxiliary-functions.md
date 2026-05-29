---
tags:
    - User-guide
    - Network
icon: lucide/function-square
---

# Auxiliary Function Files

An **auxiliary function file** (`.jfunc`) lets you attach custom symbolic expressions to a network without modifying the original network file. You use it to:

- Supply reaction-specific rate coefficients that cannot be expressed with the standard formula.
- Define composite or multi-step reactions whose effective rate coefficient depends on other species densities.
- Provide gas heating and cooling rates that vary with the physical state of the gas.
- Declare global symbolic constants shared across multiple functions.
- Define radiation generation rates per unit frequency for photo reactions

JAFF automatically looks for a file with the same stem as the network file and a `.jfunc` extension. You can also specify one explicitly:

```python
from jaff import Network

net = Network("networks/GOW/GOW.jet", funcfile="networks/GOW/GOW.jfunc")
```

Although the above examples passes the path to the auxiliary function file explicitly, JAFF automatically detects and parses a `.jfunc` file in the directory which contains the network file. The auxiliary function file **must have the same name as the network file** for this automatic detection to work. So if the network file name is `GOW.jet`, `GOW.jfunc` or `GOW.jet.jfunc` will be detected as an auxiliary functions file.

---

## File Format

A `.jfunc` file contains two kinds of declarations: **global constants** (`@var`) and **named functions** (`@function`).

### Global constants — `@var`

```text
@var name = expression
```

`expression` is a SymPy-compatible expression. It is resolved once and substituted into every function body and variable that references `name`.

```text
@var kB      = 1.380649e-16       # Boltzmann constant  (erg / K)
@var eV      = 1.602177e-12       # 1 eV in erg
@var amu     = 1.66054e-24        # 1 amu in gram
@var TCMB    = 2.73               # CMB temperature at z = 0
@var d2g_solar = 0.01             # Solar dust-to-gas ratio
```

Expressions may reference previously declared `@var` names:

```text
@var sigma_SB = 5.670374419e-5
@var c_light  = 2.99892458e10
@var a_R      = 4 * sigma_SB / c_light    # radiation constant
```

### Functions — `@function`

```text
@function name(arg1, arg2, ...)
    # optional per-argument documentation comments
    local_var = expression
    ...
    return final_expression
```

- Lines inside a function block are **local variable assignments** evaluated in order.
- The block ends with a `return` statement whose expression is the function's symbolic value.
- Comments (`#`) inside a block may document individual arguments — JAFF attaches them to the argument metadata.
- Long expressions can be wrapped with a trailing backslash `\`.
- `expressions` can contain sympy functions like `Piecewise`

Functions may call other functions defined earlier in the same file.

---

## Reserved Function Names

JAFF recognises four reserved naming conventions:

| Pattern              | Role                                                                                                                                                                                                                                         |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `chemRate<N>`        | Custom rate coefficient for reaction index _N_ (0-based). Replaces the Arrhenius expression in the network file.                                                                                                                             |
| `deltaE<N>`          | Change in gas thermal energy per occurrence of reaction _N_ (erg). Positive = exothermic.                                                                                                                                                    |
| `deltaRad<N>`        | Radiation energy source/sink term for photo-reaction _N_, as a function of photon energy `E`. Integrated over each radiation band to weigh the radiation moment equations (see [Radiation Source Terms](#radiation-source-terms-deltaradn)). |
| `heatingCoolingRate` | Net gas heating minus cooling rate from all non-chemical radiative processes (erg s⁻¹ cm⁻³).                                                                                                                                                 |
| Any other name       | Helper function — substituted symbolically into the bodies that call it.                                                                                                                                                                     |

<!-- prettier-ignore -->
!!! warning "Custom function naming"
    Once parsed, the functions are stored in lowercase formats to make them case-insensitive. This is to make sure that they are compatible with languages that are case-insensetive and must be kept in mind while naming functions

---

## Complete Example — GOW Network

The GOW (Gong, Ostriker & Wolfire 2017) network ships with a detailed `.jfunc` file. Excerpts below illustrate the full feature set.

### Global constants

```text
@var kB         = 1.380649e-16
@var c_light    = 2.99892458e10
@var sigma_SB   = 5.670374419e-5
@var a_R        = 4 * sigma_SB / c_light
@var eV         = 1.602177e-12
@var d2g_solar  = 0.01
@var TCMB       = 2.73
@var H2_OPR     = 3.0
@var f_oH2      = H2_OPR / (H2_OPR + 1)
@var f_pH2      = 1 - f_oH2
```

### Helper functions

```text
@function kcr_H_fac(nH, nH0, nH2)
    # nH   Total H nucleus density (cm^-3)
    # nH0  Neutral H atom density (cm^-3)
    # nH2  H2 molecule density (cm^-3)
    return 2.3 * (nH2/nH) + 1.5 * (nH0/nH)

@function kgr_gong(tgas, chi, av, ne, c0, c1, c2, c3, c4, c5, c6)
    # tgas Gas temperature (K)
    # chi  Radiation field (Draine 1978 units)
    # av   V-band extinction (magnitudes)
    # ne   Free electron density (cm^-3)
    # c0 c1 c2 c3 c4 c5 c6  Fitting coefficients
    psi  = 1.7 * chi * exp(-1.87 * av) * sqrt(tgas) / ne
    logT = log(tgas)
    k_gr = 1e-14 * c0 / (1 + c1 * psi**c2 * \
        (1 + c3 * tgas**c4 * psi**(-c5 - c6 * logT)))
    return k_gr
```

### Custom rate coefficients — `chemRate<N>`

Reactions whose rate cannot be written as a simple Arrhenius expression get a `chemRate<N>` function where `N` represents the 0-indexed reaction number. The arguments must match the symbolic free variables used in the expression.

```text
@function chemRate0(crate, nH, nH0, nH2)
    # Reaction 0: H + CR -> H+ + e-
    # crate  Primary ionisation rate per H nucleon (s^-1)
    return kcr_H_fac(nH, nH0, nH2) * crate

@function chemRate14(d2g, nH, nH0)
    # Reaction 14: H + H -> H2  (grain-assisted)
    # True rate = 3e-17 * nH0 * nH * (d2g / d2g_solar)
    # JAFF multiplies by the reactant densities automatically,
    # so we derive k by dividing out the extra nH0 factor.
    return 3.0e-17 * (d2g / d2g_solar) * (nH / nH0)

@function chemRate15(d2g, tgas, chi, av, nH, ne)
    # Reaction 15: H+ + e- -> H  (grain-assisted)
    c0 = 12.25
    c1 = 8.074e-6
    c2 = 1.378
    c3 = 5.087e2
    c4 = 1.586e-2
    c5 = 0.4723
    c6 = 1.102e-5
    return kgr_gong(tgas, chi, av, ne, c0, c1, c2, c3, c4, c5, c6) * \
        (d2g / d2g_solar) * nH / ne
```

### Thermal energy change — `deltaE<N>`

Functions labeled by `deltaE<N>` are used for representing the internal energy change per reaction. `N` represents the 0-indexed reaction number. The expression returned by these functions are multiplied with the reaction rate and added together to obtain the rate of internal energy change.

$$
\frac{dE}{dt} = \sum_{i} R_i \Delta E_i
$$

where $R_i$ represents the rate of the $i^{th}$ reaction and $\Delta E_i$ represents the change in internal energy per reaction

```text
@function deltaE40()
    # Reaction 40+1: H2 + H -> H + H + H  (collisional dissociation)
    return -4.48 * eV

@function deltaE13(tgas, nH, nH0, nH2, chi, av)
    # Reaction 13: H2 + photon -> H + H
    # Combined FUV-pumping + kinetic-energy heating (Visser+ 2018)
    k_photo = 5.7e-11 * chi * exp(-4.18 * av)
    f = 1 / (1 + ncrH2(tgas, nH, nH0, nH2, k_photo) / nH)
    return (0.4 + 8 * 2 * f) * eV
```

### Heating / cooling function

The heating cooling function is used to add any non-chemical heating and cooling rates to the reaction network. The returned `expresssion` must be in terms of rate of internal energy change in units of $erg\ s^{-1}$

```text
@function heatingCoolingRate(chi, av, d2g, tgas, n_H, n_H0, n_H2,
                              n_Cp, n_C0, n_O0, n_CO, n_e, gradv)
    return heating_grainPE(chi, av, d2g, tgas, n_H, n_e) \
        - cooling_LyA(n_H0, n_e, tgas) \
        - cooling_H2(n_H2, n_H0, n_Hp, n_He, n_e, tgas) \
        - cooling_Cplus(n_Cp, n_H0, n_H2, n_e, tgas) \
        - cooling_C0(n_C0, n_H0, n_H2, n_e, tgas) \
        - cooling_O0(n_O0, n_H0, n_H2, n_e, tgas) \
        - cooling_CO(n_CO, n_H0, n_H2, n_e, tgas, gradv) \
        - cooling_dust_coll(chi, av, d2g, tgas, n_H) \
        - cooling_dust_rec(chi, av, d2g, tgas, n_e)
```

---

## Radiation Source Terms — `deltaRad<N>`

When a network is loaded with radiation transport enabled (by passing `rad_bands` to `Network`), JAFF builds a set of **radiation moment equations** alongside the chemical ODEs. A `deltaRad<N>` function supplies the radiation energy (in ergs) per photon energy (in eV) that photo-reaction _N_ adds to the local field, expressed in ergs/eV.

```text
@function deltaRad5()
    # Reaction 5: local radiation energy source as a function of photon energy E
    return some_expression_in_E
```

The body must be a function of the photon-energy symbol `E`. JAFF integrates it over each radiation band, so the value represents an energy density. A reaction without a `deltaRad<N>` function contributes no radiation source to the local radiation field.

### Radiation density variable — `radeden` / `photden`

Each radiation band carries one density unknown in the generated equations. Its symbolic name depends on how the field is tracked, set by the `rad_energy_density` flag on `Network`:

| `rad_energy_density` | Density variable | Quantity tracked         | Units    |
| -------------------- | ---------------- | ------------------------ | -------- |
| `True`               | `radeden[i]`     | Radiation energy density | erg cm⁻³ |
| `False` (default)    | `photden[i]`     | Photon number density    | cm⁻³     |

Here `i` indexes the radiation band. The photo-reaction rate coefficient for band $i$ is $k_i = c \cdot den_i \cdot {\langle \sigma \rangle}_i$, where ${\langle \sigma \rangle}_i$ is the band-averaged photoionisation cross section and `c` is the speed of light. In energy-density mode the `deltaRad` contribution is divided by the band-average photon energy to convert it to the matching units.

### Custom rates and `deltaRad`

If a photo-reaction has **both** radiation transport enabled and a custom `chemRate<N>` rate, a matching `deltaRad<N>` is **required**. JAFF cannot derive the spectral weighing for the reaction rate across bands from a cross-section in that case, so it uses `deltaRad<N>` to weigh the supplied rate across the bands for radiation energy density contribution.

Thus, the reaction rate per band is weighed by

<!-- prettier-ignore -->
$$ \dfrac{\Delta rad_{band}}{\Delta rad_{spectrum}} $$

The radiation moment equations themselves are available through [`Network.sradodes()`](../../api/core/network/sradodes.md).

---

## Continuation Lines

Break long expressions across multiple lines with a trailing backslash:

```text
@function myRate(tgas, ne)
    term1 = 3.4e-8 * exp(-7.62 / tgas)
    term2 = 6.97e-9 * exp(-1.38 / tgas) + \
            1.31e-7 * exp(-26.6 / tgas) + \
            1.51e-4 * exp(-8110 / tgas)
    return (term1 + tgas**-1.5 * term2) / ne
```

---

## Supported SymPy Functions

Inside `@function` bodies and `@var` expressions you can use any SymPy built-in:

`exp`, `log`, `sqrt`, `sin`, `cos`, `tan`, `Piecewise`, `Min`, `Max`, `Abs`, `Array`, and all standard python arithmetic operators (`+`, `-`, `*`, `/`, `**`).
