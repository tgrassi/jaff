---
tags:
    - User-guide
    - Network
icon: lucide/share-2
---

# Network Formats

JAFF can currenlty parse five file formats that are standard in the astrochemical modelling community. Format detection is automatic — JAFF inspects the file content and picks the correct parser without requiring a format flag.

## Supported Formats

| Format      | Origin                                     | Paper                                                               |
| ----------- | ------------------------------------------ | ------------------------------------------------------------------- |
| **KIDA**    | Kinetic Database for Astrochemistry        | [A&A 689, A63 (2024)](https://doi.org/10.1051/0004-6361/202450606)  |
| **UDFA**    | UMIST Database for Astrochemistry (Rate22) | [A&A 682, A109 (2024)](https://doi.org/10.1051/0004-6361/202346908) |
| **PRIZMO**  | Protoplanetary disk photochemistry code    | [MNRAS 494, 4471 (2020)](https://doi.org/10.1093/mnras/staa971)     |
| **KROME**   | Astrophysical chemistry & microphysics lib | [MNRAS 439, 2386 (2014)](https://doi.org/10.1093/mnras/stu114)      |
| **UCLCHEM** | Gas-grain astrochemical Python code        | [AJ 154, 38 (2017)](https://doi.org/10.3847/1538-3881/aa773f)       |

---

## Rate Expression Variables

All rate expressions are parsed as SymPy expressions. The following physical symbols are available across all formats:

| Symbol    | Description                                      | Units         |
| --------- | ------------------------------------------------ | ------------- |
| `tgas`    | Gas temperature                                  | K             |
| `av`      | Visual extinction                                | magnitudes    |
| `crate`   | Primary cosmic-ray ionisation rate per H nucleus | s⁻¹           |
| `chi`     | Radiation field strength (Draine 1978 units)     | dimensionless |
| `ntot`    | Total number density                             | cm⁻³          |
| `hnuclei` | H nucleus number density                         | cm⁻³          |
| `d2g`     | Dust-to-gas mass ratio                           | dimensionless |
| `tdust`   | Dust grain temperature                           | K             |

Format-specific shorthand variables (e.g. `t32`, `te`, `invtgas` from KROME files) are automatically rewritten to the canonical symbols above during parsing.

---

## KIDA Format

**Source:** [kida.astrochem-tools.org/](https://kida.astrochem-tools.org/)

KIDA (Kinetic Database for Astrochemistry) distributes networks as fixed-width whitespace-separated files. Each data line encodes one reaction with its Arrhenius parameters, uncertainty estimate, reaction type, and temperature range.

### Rate formulae by `itype`

| `itype` | Reaction class                         | Rate expression                                                   |
| ------- | -------------------------------------- | ----------------------------------------------------------------- |
| 1       | Direct CR ionisation                   | $\alpha \cdot \zeta$                                              |
| 2       | CR-induced UV photodissociation        | $\alpha \cdot \zeta$                                              |
| 3       | FUV dissociation / ionisation          | $\alpha \cdot \chi \cdot e^{-\beta A_V}$                          |
| 4       | Neutral-neutral / ion-neutral          | $\alpha \left(\dfrac{T}{300}\right)^\beta e^{-\dfrac{\gamma}{T}}$ |
| 5       | Charge-exchange                        | $\alpha \left(\dfrac{T}{300}\right)^\beta e^{-\dfrac{\gamma}{T}}$ |
| 6       | Radiative association                  | $\alpha \left(\dfrac{T}{300}\right)^\beta e^{-\dfrac{\gamma}{T}}$ |
| 7       | Associative detachment                 | $\alpha \left(\dfrac{T}{300}\right)^\beta e^{-\dfrac{\gamma}{T}}$ |
| 8       | Dissociative / radiative recombination | $\alpha \left(\dfrac{T}{300}\right)^\beta e^{-\dfrac{\gamma}{T}}$ |
| 9       | Grain-assisted reactions               | network-specific                                                  |
| 10      | Special / composite reactions          | network-specific                                                  |

### Column layout

```text
Reactant1  Reactant2          Product1   Product2   α         β         γ        F    g   err  ni  Tmin  Tmax  frml  ID  ...
```

### Example

A comprehensive example of the KIDA format implementation can be found in `networks/GOW/GOW.jet`

```text
! comment lines start with '!'
! alpha, beta, gamma: Arrhenius coefficients
! itype: reaction type (see KIDA documentation)
! Tmin, Tmax: valid temperature range

H          CR                     H+         e-        0.000e+00  0.000e+00  0.000e+00 2.00e+00 0.00e+00 logn  1  -9999   9999  7     1 1  1
H2         CR                     H2+        e-        0.000e+00  0.000e+00  0.000e+00 2.00e+00 0.00e+00 logn  1  -9999   9999  7     2 1  1
He         CR                     He+        e-        1.100e+00  0.000e+00  0.000e+00 2.00e+00 0.00e+00 logn  1  -9999   9999  1     3 1  1
```

---

## UDFA Format

**Source:** [umistdatabase.uk](https://umistdatabase.uk/)

The UMIST Database for Astrochemistry (Rate22) uses a colon-delimited format with a leading integer ID and reaction-type tag. Up to three reactants and four products are supported; unused slots are left empty between consecutive colons.

### Column layout

```text
ID:type:R1:R2:R3:P1:P2:P3:P4:α:β:γ:Tmin:Tmax:...
```

| Field       | Description                                       |
| ----------- | ------------------------------------------------- |
| `ID`        | Integer reaction index                            |
| `type`      | Reaction class code (e.g. `AD`, `IN`, `RA`, `DR`) |
| `R1–R3`     | Reactants (empty if fewer than 3)                 |
| `P1–P4`     | Products (empty if fewer than 4)                  |
| `α β γ`     | Arrhenius parameters                              |
| `Tmin Tmax` | Valid temperature range (K)                       |

### Example

A comprehensive example of the UDFA format implementation can be found in `networks/rate22_final/rate22_final.rates.jet`

```text
1:AD:C-:C:C2:e-:::1:5.00e-10:0.00:0.0:10:41000:L:C:"10.1086/190665":"Prasad and Huntress 1980":
2:AD:C-:CH2:C2H2:e-:::1:5.00e-10:0.00:0.0:10:41000:L:C:"10.1086/190665":"Prasad and Huntress 1980":
3:AD:C-:CH:C2H:e-:::1:5.00e-10:0.00:0.0:10:41000:L:C:"10.1086/190665":"Prasad and Huntress 1980":
```

---

## PRIZMO Format

**Source:** [tgrassi.prizmo](https://github.com/tgrassi/prizmo)

PRIZMO networks are Fortran-flavoured text files with an optional `VARIABLES{}` block at the top. Inside the block, shorthand aliases are defined and then used in the rate expressions on subsequent reaction lines. JAFF converts Fortran double-precision literals (`d` exponent) and exponent operators (`**`) to Python/SymPy automatically.

### `VARIABLES{}` block

```text
VARIABLES{
    variable_name = expression
    ...
}
```

Variables can reference each other and the standard physical symbols (`tgas`, `av`, etc.).

### Reaction line syntax

```text
Reactant1 [+ Reactant2] -> Product1 [+ Product2 ...]    rate_expression
```

### Photoreaction syntax

Photo reactions can be specified by using the `PHOTO` keyword in the rate expresssion separated by a comma. The `PHOTO` keyword is case sensitive

```text
H -> H+ + E    []    PHOTO, 13.60
```

### Example

```text
# custom variables can be defined this way
VARIABLES{
    invt  = 1d0 / Tgas
    t32   = Tgas / 3d2
    sqrtt = sqrt(Tgas)
}

H + O -> OH        1.2d-10 * sqrtt
CO -> C + O        1.0d-10 * exp(-3.53d0 * av)
```

---

## KROME Format

**Source:** [kromepackage.org](https://kromepackage.org/)

KROME files open with a `@format:` header that specifies column semantics, followed by comma-separated reaction lines. Global Fortran-style variable aliases can be defined with `@var:`. Other KROME decleratives are ignored.

### `@format:` header

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate
```

Tokens: `idx` (index), `R` (reactant), `P` (product), `tmin`/`tmax` (temperature bounds, K), `rate` (reaction rate coefficient).

### Variable aliases

```text
@var:te      = tgas * 8.617343e-5    ! electron temperature in eV
@var:invtgas = 1e0 / tgas
@var:t32     = tgas / 3e2
```

### Example

A comprehensive example can be found at `networks/COthin/react_COthin.jet`

```text
#rates for CO network similar to Glover+2010
@var:Hnuclei = get_Hnuclei(n(:))
@common: user_crate, user_Av, user_Tdust

@var:Te = Tgas * 8.617343d-5

1,H,,,OH,,,, 10,1e4, 1.2e-10 * (tgas/300)**0.5
2,H2,O,,OH,H,, 10,1e4, 3.4e-11 * exp(-500/tgas)
```

---

## UCLCHEM Format

**Source:** [uclchem.github.io](https://uclchem.github.io/)

UCLCHEM networks use the same `!`-prefixed comment style but with a distinct column layout produced by the UCLCHEM Python tool. Gas-phase species have no prefix; ice-surface species are prefixed with `#`, bulk-ice species with `@` and so on.

### Column layout

```text
R1  R2  [R3]  P1  P2  [P3]  [P4]  α  β  γ  Tmin  Tmax  itype  ID ...
```

### Example

A comprehensive example can be found at `networks/uclchem_small_gas/uclchem_small_gas_network.jet`

```text
!
! Small gas network from UCLCHEM v3.5.1
! Species notation: @ = bulk ice, # = surface ice, no prefix = gas phase
!

N2         CR                     N          N         5.000e+00  0.000e+00  0.000e+00 1.25e+00 0.00e+00 logn  1  -9999   9999  1     1 1  1
H          CR                     H+         e-        4.600e-01  0.000e+00  0.000e+00 2.00e+00 0.00e+00 logn  1  -9999   9999  1     2 1  1
He         CR                     He+        e-        5.000e-01  0.000e+00  0.000e+00 2.00e+00 0.00e+00 logn  1  -9999   9999  1     3 1  1
```

---

## Using these formats in JAFF

Since these formats are simple text files, JAFF can read any of these formats irrespective of the file name extension. However, it is recommended to use the `.jet` extension for JAFF networks for the sole purpose of consistency. Network formats in JAFF can also be combined in a single file and JAFF will be able to correctly detect and parse that format.

### Example

An example of combined reaction formats can be found at `networks/demos/demo1.jet`

```text
VARIABLES{
    invt = 1d0 / Tgas
    t32 = Tgas / 3d2
}

H+ + E -> H                    [0, 300]   3.61e-12*t32**(-0.75)

# KIDA format
N2         CR                     N          N                                             5.000e+00  0.000e+00  0.000e+00 1.25e+00 0.00e+00 logn  1  -9999   9999  1     1 1  1

# UMIST format
326:CE:CO:N2+:N2:CO+:::1:7.40e-11:0.00:0.0:10:41000:M:A:"10.1063/1.438893"::

# KROME format (default)
16,H2,E,,H,H,E,,NONE,NONE,5.6e-11*exp(-102124e0*invT)*Tgas**0.5

# KROME format (custom)
@format:R,R,P,P,rate
CO,N2+,N2,CO+,4.3e-13
```
