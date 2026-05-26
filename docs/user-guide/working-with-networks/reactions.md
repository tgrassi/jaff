---
tags:
    - User-guide
    - Reaction
icon: lucide/zap
---

# Reactions

JAFF stores every reaction from the network as a `Reaction` object inside the `Reactions` catalogue. Both are available from the loaded network.

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")

for rxn in net.reactions:
    print(rxn.verbatim, "  k =", rxn.rate)
```

---

## `Reaction` Attributes

| Attribute            | Type           | Description |
| -------------------- | -------------- | ----------- |
| `verbatim`           | `str`          | Human-readable equation (e.g. `"H -> H+ + E"`) |
| `reactants`          | `list[Specie]` | Reactant species objects |
| `products`           | `list[Specie]` | Product species objects |
| `rate`               | `sympy.Expr`   | Symbolic rate coefficient expression |
| `tmin`               | `float\|None`  | Minimum valid temperature (K) |
| `tmax`               | `float\|None`  | Maximum valid temperature (K) |
| `dE`                 | `sympy.Expr`   | Thermal energy change per occurrence (erg), from `.jfunc` |
| `index`              | `int`          | Zero-based position in the reactions array |
| `xsecs`              | `dict\|None`   | Cross-section data for photochemical reactions |

```python
rxn = net.reactions[0]
print(rxn.verbatim)            # H -> H+ + E
print(rxn.rate)                # symbolic expression
print(rxn.tmin, rxn.tmax)     # None None
print(rxn.index)               # 0
```

---

## Accessing Reactions

### By index

```python
rxn = net.reactions[0]
rxn = net.reactions[-1]        # last reaction
```

### By verbatim string

```python
rxn = net.reactions["H -> H+ + E"]
```

### Iteration

```python
for rxn in net.reactions:
    print(f"{rxn.index:4d}  {rxn.verbatim}")
```

### Count

```python
net.reactions.count   # int
```

---

## `Reactions` Collection Methods

### Bulk data access

```python
net.reactions.verbatim()              # list[str]   — verbatim strings for all reactions
net.reactions.rates()                 # list[Expr]  — rate expressions
net.reactions.tmins()                 # list[float] — minimum temperatures
net.reactions.tmaxes()                # list[float] — maximum temperatures
net.reactions.reactants()             # list[list]  — reactant name lists
net.reactions.products()              # list[list]  — product name lists
net.reactions.rtypes()                # list[str]   — reaction type strings
```

### Photochemical reactions

```python
photo = net.reactions.photo_reactions()         # Reactions — subset of photo reactions
truths = net.reactions.photo_reaction_truths()  # list[int] — 1 if photo, else 0
indices = net.reactions.photo_reaction_indices() # list[int] — positions of photo reactions
```

### Filter by type

```python
cr_reactions = net.reactions.with_rtype("CR")   # cosmic-ray reactions
```

---

## `Reaction` Methods

### Conservation checks

```python
rxn = net.reactions[0]

ok_mass   = rxn.check_mass()    # bool
ok_charge = rxn.check_charge()  # bool
ok_both   = rxn.check()         # bool — both together
```

### Species membership

```python
rxn.has_reactant("H")          # bool
rxn.has_product("H+")          # bool
rxn.has_any_species("H")       # bool — reactant or product
```

### Isomer detection

```python
rxn2 = net.reactions[5]
same_composition = rxn.is_isomer_version(rxn2)   # bool
```

### String representations

```python
rxn.verbatim              # "H -> H+ + E"
rxn.get_verbatim()        # same as above
rxn.get_latex()           # "${\rm H} \to {\rm H^+} + {\rm E}$"
rxn.serialize()           # "H__Hplus_E"
rxn.serialize_exploded()  # uses atomic composition
```

### Code generation

```python
# Rate coefficient as code string
rxn.get_code(lang="python")   # Python expression
rxn.get_code(lang="cxx")      # C++ expression
rxn.get_code(lang="fortran")  # Fortran expression
rxn.get_code(lang="rust")     # Rust expression
rxn.get_code(lang="julia")    # Julia expression
rxn.get_code(lang="r")        # R expression

# Flux expression: rate × reactant densities
rxn.get_flux_expression(
    idx=0,
    rate_variable="k",
    species_variable="nden",
    brackets="[]",
)
```

### Symbolic form

```python
import sympy

expr = rxn.get_sympy()                 # full symbolic rate expression
tgas = sympy.Symbol("tgas")
drdt = sympy.diff(expr, tgas)          # analytical temperature derivative
```

### Plotting

```python
# Rate vs temperature
rxn.plot()

# Cross-section vs energy (photochemical reactions)
rxn.plot_xsecs()                       # energy in eV (default)
rxn.plot_xsecs(energy_unit="nm")       # wavelength in nm
```

---

## Common Patterns

### Conservation audit

```python
errors = []
for rxn in net.reactions:
    if not rxn.check():
        errors.append(rxn.verbatim)

if errors:
    print(f"Conservation failures ({len(errors)}):")
    for v in errors:
        print(f"  {v}")
else:
    print("All reactions pass conservation checks.")
```

### Formation and destruction pathways

```python
def pathways(net, species_name):
    formed    = [r for r in net.reactions if r.has_product(species_name)]
    destroyed = [r for r in net.reactions if r.has_reactant(species_name)]
    print(f"\n{species_name}: {len(formed)} formation / {len(destroyed)} destruction")
    print("  Formation:")
    for r in formed[:5]:
        print(f"    {r.verbatim}")
    print("  Destruction:")
    for r in destroyed[:5]:
        print(f"    {r.verbatim}")

pathways(net, "CO")
```

### Export to CSV

```python
import csv

with open("reactions.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["index", "reaction", "tmin", "tmax", "n_reactants", "n_products"])
    for rxn in net.reactions:
        w.writerow([
            rxn.index, rxn.verbatim,
            rxn.tmin, rxn.tmax,
            len(rxn.reactants), len(rxn.products),
        ])
```
