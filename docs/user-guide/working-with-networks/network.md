---
tags:
    - User-guide
    - Network
icon: lucide/flask-conical
---

# Network

`Network` is the primary entry point for every JAFF workflow. It reads a reaction network file, validates it, builds typed catalogues for species, reactions, and elements, and exposes symbolic ODE expressions for downstream code generation.

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")
```

---

## Constructor

```python
Network(
    fname,
    errors=False,
    label=None,
    funcfile=None,
    replace_nH=True,
    rad_bands=[],
    rad_powerlaw_index=0,
    rad_energy_density=False,
)
```

| Parameter           | Type                    | Default | Description |
| ------------------- | ----------------------- | ------- | ----------- |
| `fname`             | `str \| Path`           | —       | Path to the network file (required) |
| `errors`            | `bool`                  | `False` | Raise on conservation violations instead of warning |
| `label`             | `str \| None`           | `None`  | Human-readable network name (defaults to file stem) |
| `funcfile`          | `str \| Path \| None`   | `None`  | Path to a `.jfunc` auxiliary function file; auto-detected when `None`; pass `"none"` to skip |
| `replace_nH`        | `bool`                  | `True`  | Expand `nh` / `nhe` shorthand to sums of `nden[i]` terms |
| `rad_bands`         | `list`                  | `[]`    | Radiation band boundaries in eV; empty list disables photochemistry |
| `rad_powerlaw_index`| `int \| float`          | `0`     | Power-law spectral index for band integration |
| `rad_energy_density`| `bool`                  | `False` | Use energy density (`True`) or photon density (`False`) for radiation moments |

### Examples

```python
# Minimal load
net = Network("networks/GOW/GOW.jet")

# Strict validation
net = Network("networks/GOW/GOW.jet", errors=True)

# Custom label and funcfile
net = Network(
    "networks/GOW/GOW.jet",
    label="GOW-2017",
    funcfile="networks/GOW/GOW.jfunc",
)

# With radiation bands (photochemistry)
net = Network(
    "networks/h_photoionization/h_photo.jet",
    rad_bands=[13.6, float("inf")],
    rad_powerlaw_index=0,
    rad_energy_density=False,
)
```

---

## Key Attributes

| Attribute          | Type              | Description |
| ------------------ | ----------------- | ----------- |
| `file_name`        | `Path`            | Absolute path to the source file |
| `label`            | `str`             | Network name |
| `species`          | `Species`         | Ordered species catalogue |
| `reactions`        | `Reactions`       | Ordered reaction catalogue |
| `elements`         | `Elements`        | Element catalogue derived from species |
| `reactant_matrix`  | `np.ndarray`      | Integer stoichiometry matrix, shape `(n_reactions, n_species)` — reactants |
| `product_matrix`   | `np.ndarray`      | Integer stoichiometry matrix — products |
| `dEdt_chem`        | `sympy.Basic`     | Symbolic total chemical heating/cooling rate (erg cm⁻³ s⁻¹) |
| `dEdt_other`       | `sympy.Basic`     | Additional heating/cooling from `heatingCoolingRate` in `.jfunc` |
| `radiation`        | `Radiation\|None` | Radiation field object; `None` when no bands are configured |

```python
print(net.label)                     # "h_photo"
print(net.species.count)             # 3
print(net.reactions.count)           # 2
print(net.reactant_matrix.shape)     # (2, 3)
```

---

## Symbolic Expressions

### Species ODEs

```python
# Symbolic ODE system (dict: species -> derivative expression)
odes = net.sodes()
for specie, expr in odes.items():
    print(f"d[{specie}]/dt = {expr}")
```

### Flux expressions

```python
# Flux (reaction rate × reactant densities) for each reaction
fluxes = net.sfluxes()
for reaction, flux in fluxes.items():
    print(f"flux({reaction}) = {flux}")
```

### Radiation ODEs

```python
# Only available when rad_bands are configured
if net.radiation:
    radodes = net.sradodes()
    for band, expr in radodes.items():
        print(f"d[rad_{band}]/dt = {expr}")
```

---

## Validation

JAFF validates mass and charge conservation automatically during loading. With `errors=False` (default), violations emit warnings. With `errors=True`, the process exits on first violation.

```python
# Check for duplicate reactions
dupes = net.check_unique_reactions()

# Check for sink/source species (species with only destruction or only formation)
sinks, sources = net.check_sink_sources()

# Check recombination balance
net.check_recombinations()

# Check isomers
isomers = net.check_isomers()

# Compare two networks
net2 = Network("networks/GOW/GOW_v2.jet")
diff_reactions = net.compare_reactions(net2)
diff_species   = net.compare_species(net2)
```

---

## Export

### HDF5 rate tables

```python
net.to_hdf5(
    fname="rates.h5",
    T_min=10,
    T_max=1e4,
    nT=200,
    err_tol=1e-3,   # adaptive sampling tolerance; None = fixed grid
)
```

### Plain-text rate tables

```python
net.to_txt(
    fname="rates.txt",
    T_min=10,
    T_max=1e4,
    nT=200,
    fast_log=False,
    include_all=False,
    verbose=False,
)
```

### JAFF binary format

```python
# Export to gzip-compressed JSON .jaff file
net.to_jaff("network.jaff")

# Re-load from .jaff file
net2 = Network("network.jaff")
```

---

## Free Symbols

Query which symbolic variables appear in the rate expressions:

```python
# All free symbols across all reactions
syms = net.free_symbols()
print(syms)  # {tgas, av, crate, nden[0, 0], nden[1, 0], ...}
```
