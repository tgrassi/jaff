---
tags:
    - User-guide
    - Network
icon: lucide/share-2
---

# Network Formats

JAFF parses five file formats that are standard in the astrochemical modelling community. Format detection is automatic — JAFF inspects the file content and picks the correct parser without requiring a format flag.

## Supported Formats

| Format      | Origin                                      | Detection trigger          | Paper |
| ----------- | ------------------------------------------- | -------------------------- | ----- |
| **KIDA**    | Kinetic Database for Astrochemistry         | `!`-comments + column layout | [A&A 689, A63 (2024)](https://doi.org/10.1051/0004-6361/202450606) |
| **UDFA**    | UMIST Database for Astrochemistry (Rate22)  | Colon-separated ID prefix    | [A&A 682, A109 (2024)](https://doi.org/10.1051/0004-6361/202346908) |
| **PRIZMO**  | Protoplanetary disk photochemistry code     | `VARIABLES{` block           | [MNRAS 494, 4471 (2020)](https://doi.org/10.1093/mnras/staa971) |
| **KROME**   | Astrophysical chemistry & microphysics lib  | `@format:` header line       | [MNRAS 439, 2386 (2014)](https://doi.org/10.1093/mnras/stu114) |
| **UCLCHEM** | Gas-grain astrochemical Python code         | `!`-comments + UCLCHEM header | [AJ 154, 38 (2017)](https://doi.org/10.3847/1538-3881/aa773f) |

---

## Rate Expression Variables

All rate expressions are parsed as SymPy expressions. The following physical symbols are available across all formats:

| Symbol    | Description                                           | Units         |
| --------- | ----------------------------------------------------- | ------------- |
| `tgas`    | Gas temperature                                       | K             |
| `av`      | Visual extinction                                     | magnitudes    |
| `crate`   | Primary cosmic-ray ionisation rate per H nucleus      | s⁻¹           |
| `chi`     | Radiation field strength (Draine 1978 units)          | dimensionless |
| `ntot`    | Total number density                                  | cm⁻³          |
| `hnuclei` | H nucleus number density                              | cm⁻³          |
| `d2g`     | Dust-to-gas mass ratio                                | dimensionless |
| `tdust`   | Dust grain temperature                                | K             |

Format-specific shorthand variables (e.g. `t32`, `te`, `invtgas` from KROME files) are automatically rewritten to the canonical symbols above during parsing.

---

## KIDA Format

**Source:** [kida.obs.u-bordeaux1.fr](https://kida.obs.u-bordeaux1.fr/)

KIDA (Kinetic Database for Astrochemistry) distributes networks as fixed-width whitespace-separated files with `!`-prefixed comment lines. Each data line encodes one reaction with its Arrhenius parameters, uncertainty estimate, reaction type, and temperature range.

### Rate formulae by `itype`

| `itype` | Reaction class                       | Rate expression |
| ------- | ------------------------------------ | --------------- |
| 1       | Direct CR ionisation                 | $\alpha \cdot \zeta$ |
| 2       | CR-induced UV photodissociation      | $\alpha \cdot \zeta$ |
| 3       | FUV dissociation / ionisation        | $\alpha \cdot \chi \cdot e^{-\beta A_V}$ |
| 4       | Neutral-neutral / ion-neutral        | $\alpha (T/300)^\beta e^{-\gamma/T}$ |
| 5       | Charge-exchange                      | $\alpha (T/300)^\beta e^{-\gamma/T}$ |
| 6       | Radiative association                | $\alpha (T/300)^\beta e^{-\gamma/T}$ |
| 7       | Associative detachment               | $\alpha (T/300)^\beta e^{-\gamma/T}$ |
| 8       | Dissociative / radiative recombination | $\alpha (T/300)^\beta e^{-\gamma/T}$ |
| 9       | Grain-assisted reactions             | network-specific |
| 10      | Special / composite reactions        | network-specific |

### Column layout

```text
Reactant1  Reactant2          Product1   Product2   α         β         γ        F    g   err  ni  Tmin  Tmax  frml  ID  ...
```

### Example (GOW network)

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

**Source:** [udfa.ajmarkwick.net](https://udfa.ajmarkwick.net/)

The UMIST Database for Astrochemistry (Rate22) uses a colon-delimited format with a leading integer ID and reaction-type tag. Up to three reactants and four products are supported; unused slots are left empty between consecutive colons.

### Column layout

```text
ID:type:R1:R2:R3:P1:P2:P3:P4:α:β:γ:Tmin:Tmax:...
```

| Field   | Description |
| ------- | ----------- |
| `ID`    | Integer reaction index |
| `type`  | Reaction class code (e.g. `AD`, `IN`, `RA`, `DR`) |
| `R1–R3` | Reactants (empty if fewer than 3) |
| `P1–P4` | Products (empty if fewer than 4) |
| `α β γ` | Arrhenius parameters |
| `Tmin Tmax` | Valid temperature range (K) |

### Example (Rate22)

```text
1:AD:C-:C:C2:e-:::1:5.00e-10:0.00:0.0:10:41000:L:C:"10.1086/190665":"Prasad and Huntress 1980":
2:AD:C-:CH2:C2H2:e-:::1:5.00e-10:0.00:0.0:10:41000:L:C:"10.1086/190665":"Prasad and Huntress 1980":
3:AD:C-:CH:C2H:e-:::1:5.00e-10:0.00:0.0:10:41000:L:C:"10.1086/190665":"Prasad and Huntress 1980":
```

---

## PRIZMO Format

**Source:** [prizmo.astrophysics.it](https://prizmo.astrophysics.it/)

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

KROME files open with a `@format:` header that specifies column semantics, followed by comma-separated reaction lines. Global Fortran-style variable aliases can be defined with `@var:`, and shared physical quantities can be declared with `@common:`.

### `@format:` header

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate
```

Tokens: `idx` (index), `R` (reactant), `P` (product), `tmin`/`tmax` (temperature bounds, K), `rate` (SymPy expression string).

### Variable aliases

```text
@var:te      = tgas * 8.617343e-5    ! electron temperature in eV
@var:invtgas = 1e0 / tgas
@var:t32     = tgas / 3e2
```

### Example (COthin network)

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

UCLCHEM networks use the same `!`-prefixed comment style as KIDA but with a distinct column layout produced by the UCLCHEM Python tool. Gas-phase species have no prefix; ice-surface species are prefixed with `#`, and bulk-ice species with `@`.

### Column layout

```text
R1  R2  [R3]  P1  P2  [P3]  [P4]  α  β  γ  Tmin  Tmax  itype  ID ...
```

### Example (small gas network)

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

## JAFF Native Format (`.jet`)

In addition to the formats above, JAFF also reads its own native `.jet` format. This is a minimal human-writable syntax that is not tied to any external database.

### Reaction line syntax

```text
Reactant1 [+ Reactant2 ...] -> Product1 [+ Product2 ...]    [label_list]    rate_expression
```

The optional `[label_list]` is a bracket-enclosed comma-separated list of string tags.

### Photoreaction syntax

```text
H -> H+ + E    []    PHOTO, 13.60
```

`PHOTO` followed by the ionisation / dissociation threshold energy (eV) triggers the photochemistry pipeline (see [Photochemistry](photochemistry.md)).

### Example (H photoionisation)

```text
H -> H+ + E          []         PHOTO, 13.60
H+ + E -> H          []         2.63e-13 * (tgas / 1e4)**(-0.7)
```

### General rate example

```text
E + CO+ -> CO        []         2e-12 * tgas**0.33
CO -> CO+ + E        []         1e-12 * exp(-1.222 * av)
```
