---
tags:
    - User-guide
    - Network
icon: lucide/share-2
---

# Network File Formats

## Overview

JAFF supports multiple file formats used in astrochemistry. Each format has its own syntax and conventions, but JAFF automatically detects and parses them correctly.

**Supported Formats:**

| Format    | Origin         | Auto-detect        |
| --------- | -------------- | ------------------ |
| `KROME`   | KROME code     | `@format:` line    |
| `KIDA`    | KIDA database  | Colon separators   |
| `UDFA`    | UMIST database | Colon format       |
| `PRIZMO`  | PRIZMO code    | `VARIABLES{` block |
| `UCLCHEM` | UCL_CHEM       | `,NAN,` markers    |

JAFF supports SymPy expressions with these variables:

- `tgas`: Gas temperature (K)
- `av`: Visual extinction
- `crate`: Cosmic rate ionization of $H_2$ in $s^{-1}$
- `ntot`: Total number density in $cm^{-1}$
- `hnuclei`: H nuclei number density in $cm^{-1}$
- `d2g`: Dust-to-gas mass ratio again

## KROME Format

Format used by the KROME astrochemistry package.

### Syntax

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate
idx,Reactant1,Reactant2,Reactant3,Product1,Product2,Product3,Product4,Tmin,Tmax,Rate
```

### Format Specification

The `@format:` line defines column meanings:

- `idx`: Reaction index (integer)
- `R`: Reactant (up to 3)
- `P`: Product (up to 4)
- `tmin`: Minimum temperature (K)
- `tmax`: Maximum temperature (K)
- `rate`: Rate expression

### Example

```text
@format:idx,R,R,R,P,P,P,P,tmin,tmax,rate

# Reaction data
1,H,O,,,OH,,,10,1e4,1.2e-10*(T/300)**0.5
2,H2,O,,,OH,H,,10,1e4,3.4e-11*exp(-500/T)
3,C,O2,,,CO,O,,10,1e4,5.6e-12

# Three-body reactions (third body is last reactant)
4,H,H,H2,H2,,,,10,300,1.0e-32*(T/300)**(-0.6)
```

### Variables

KROME supports variable definitions:

```text
@var:te=tgas*8.617343e-5
@var:invtgas=1.0/tgas
@var:sqrtgas=sqrt(tgas)

1,H,O,,,OH,,,10,1e4,1.2e-10*sqrtgas
```

### Temperature Limits

Rate expressions are clamped to `[tmin, tmax]`:

```text
# This reaction only applies between 100K and 1000K
1,H,O,,,OH,,,100,1000,1.2e-10*(T/300)**0.5
```

When temperature is outside range:

- `T < Tmin`: Rate evaluated at `Tmin`
- `T > Tmax`: Rate evaluated at `Tmax`

## KIDA Format

Format from the Kinetic Database for Astrochemistry.

### Syntax

```text
Reactants -> Products : α : β : γ
```

**Rate formula:** $k(T) = \alpha \times (T/300)^\beta \times e^{(-\gamma/T)}$

### Example

```text
H + O -> OH : 1.2e-10 : 0.5 : 0.0
H2 + O -> OH + H : 3.4e-11 : 0.0 : 500.0
C + O2 -> CO + O : 5.6e-12 : 0.0 : 0.0
```

### Parameters

- **$\alpha$**: Pre-exponential factor (cm³/s for 2-body)
- **$\beta$**: Temperature exponent
- **$\gamma$**: Activation energy parameter (K)

### Temperature Dependence

```text
# No temperature dependence (β=0, γ=0)
C + O -> CO : 5.0e-11 : 0 : 0

# Power law only (γ=0)
H + O -> OH : 1.2e-10 : 0.5 : 0

# Exponential only (β=0)
H2 + O -> OH + H : 3.4e-11 : 0 : 500

# Both power law and exponential
OH + H2 -> H2O + H : 2.1e-11 : 0.5 : 1000
```

## UDFA Format

Format from the UMIST Database for Astrochemistry.

### Syntax

```text
R1:R2:R3:P1:P2:P3:P4:α:β:γ:Tmin:Tmax
```

Colon-separated format with all fields.

### Example

```text
H:O:::OH::::1.2e-10:0.5:0.0:10:1e4
H2:O:::OH:H:::3.4e-11:0.0:500.0:10:1e4
C:O2:::CO:O:::5.6e-12:0.0:0.0:10:1e4
```

### Field Order

- 1-3: Reactants (empty if fewer than 3)
- 4-7: Products (empty if fewer than 4)
- 8: $\alpha$ (pre-exponential factor)
- 9: $\beta$ (temperature exponent)
- 10: $\gamma$ (activation energy)
- 11: Tmin (minimum temperature)
- 12: Tmax (maximum temperature)

### Empty Fields

Use empty strings for missing reactants/products:

```text
# Single reactant, single product
CO::::C:O:::1.0e-10:0:0:10:1e4

# Two reactants, two products
H:O2:::OH:O:::2.0e-11:0:100:10:1e4
```

## PRIZMO Format

Format used by the PRIZMO code.

### Syntax

```text
VARIABLES{
    variable1 = expression1
    variable2 = expression2
}

Reactants -> Products, rate_expression
```

### Example

```text
VARIABLES{
    k1 = 1.2e-10
    k2 = 3.4e-11
    sqrtt = sqrt(tgas)
    expt = exp(-500/tgas)
}

H + O -> OH, k1 * sqrtt
H2 + O -> OH + H, k2 * expt
C + O2 -> CO + O, 5.6e-12
```

### Variable Block

Variables defined in `VARIABLES{}` block:

```text
VARIABLES{
    # Temperature variables
    t32 = tgas / 300
    invt = 1.0 / tgas

    # Common rate factors
    k_neutral = 1.0e-10 * sqrt(tgas)
    k_ion = 1.0e-9
}
```

Variables can reference each other:

```text
VARIABLES{
    t32 = tgas / 300
    sqrtt32 = sqrt(t32)
    rate_base = 1.0e-10 * sqrtt32
}
```

### Fortran Expressions

PRIZMO uses Fortran syntax:

```text
VARIABLES{
    # Fortran-style exponentiation
    t32 = tgas / 3.0e2

    # Double precision literals
    k1 = 1.0d-10
    k2 = 3.4d-11
}
```

JAFF automatically converts this to Python syntax.

## UCLCHEM Format

Format from the UCLCHEM code.

### Syntax

```text
R1,R2,R3,P1,P2,P3,P4,α,β,γ
```

Comma-separated with `NAN` placeholders.

### Example

```text
H,O,NAN,OH,NAN,NAN,NAN,1.2e-10,0.5,0.0
H2,O,NAN,OH,H,NAN,NAN,3.4e-11,0.0,500.0
C,O2,NAN,CO,O,NAN,NAN,5.6e-12,0.0,0.0
```

### NAN Placeholders

Use `NAN` for empty slots:

```text
# Single reactant
CO,NAN,NAN,C,O,NAN,NAN,1.0e-10,0,0

# Two reactants, single product
H,H,NAN,H2,NAN,NAN,NAN,1.0e-32,-0.6,0
```

### Field Order

Fields: R1, R2, R3, P1, P2, P3, P4, α, β, γ

Always 10 comma-separated values per line.

## Format Comparison

### Rate Expression Styles

| Format   | Expression Style | Example                |
| -------- | ---------------- | ---------------------- |
| KROME    | Fortran          | `1.2e-10*(T/300)**0.5` |
| KIDA     | Parameters       | `1.2e-10 : 0.5 : 0`    |
| UDFA     | Parameters       | `1.2e-10:0.5:0`        |
| PRIZMO   | Fortran          | `k1 * sqrtt`           |
| UCL_CHEM | Parameters       | `1.2e-10,0.5,0`        |

## Photoreactions

Different formats handle photoreactions differently.

### JAFF Format

```text
CO + Photon -> C + O, photo(CO, 1e-10)
H2O + hν -> OH + H, photo(H2O, 2e-10)
```

### KROME Format

```text
@format:idx,R,R,P,P,rate
1,CO,Photon,C,O,photo(1e-10,1e99)
```

### KIDA Format

```text
CO + Photon -> C + O : photo : 1e-10 : 0
```

## See Also

- [Loading Networks](loading-networks.md) - How to load networks
- [Network API](../api/network.md) - Network class reference

---

**Next:** Learn about [Working with Species](species.md).
