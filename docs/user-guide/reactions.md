---
tags:
    - User-guide
    - Reaction
icon: lucide/zap
---

# Working with Reactions

## Overview

Reactions describe how chemical species transform from reactants to products. Each reaction has an associated rate expression that determines how fast the transformation occurs.

```python
from jaff import Network

# Load a network
net = Network("networks/react_COthin")

# Access reactions
for rxn in net.reactions:
    print(f"{rxn.verbatim}")
    print(f"  Type: {rxn.guess_type()}")
    print(f"  Rate: {rxn.rate}")
```

## Reaction Attributes

Each reaction object has the following attributes:

| Attribute             | Type          | Description                                    |
| --------------------- | ------------- | ---------------------------------------------- |
| `reactants`           | list          | List of Species objects consumed               |
| `products`            | list          | List of Species objects produced               |
| `rate`                | sympy.Expr    | Symbolic expression for the reaction rate      |
| `tmin`                | float or None | Minimum temperature (K)                        |
| `tmax`                | float or None | Maximum temperature (K)                        |
| `dE`                  | float         | Energy change or activation energy             |
| `verbatim`            | str           | Human-readable equation (e.g., "H + H -> H2")  |
| `serialized`          | str           | Serialized form using species names            |
| `serialized_exploded` | str           | Serialized form using atomic composition       |
| `xsecs`               | dict or None  | Cross-section data for photochemical reactions |

## Accessing Reactions

### By Index

```python
# Get first reaction
rxn = net.reactions[0]
print(f"First reaction: {rxn.verbatim}")

# Iterate over all reactions
for i, rxn in enumerate(net.reactions):
    print(f"{i}: {rxn.verbatim}")
```

### Count Reactions

```python
total = len(net.reactions)
print(f"Network has {total} reactions")
```

## Filtering Reactions

### By Reaction Type

```python
# Find photochemical reactions
photo_rxns = [r for r in net.reactions if r.guess_type() == "photo"]
print(f"Found {len(photo_rxns)} photochemical reactions")

# Find cosmic ray reactions
cr_rxns = [r for r in net.reactions if r.guess_type() == "cosmic_ray"]

# Find three-body reactions
tb_rxns = [r for r in net.reactions if r.guess_type() == "3_body"]

# Find reactions with visual extinction dependence
av_rxns = [r for r in net.reactions if r.guess_type() == "photo_av"]
```

### By Species Involvement

```python
# Find all reactions involving H2
h2_reactions = [r for r in net.reactions if r.has_any_species("H2")]

# Find reactions that consume H2
h2_destruction = [r for r in net.reactions if r.has_reactant("H2")]

# Find reactions that produce H2
h2_formation = [r for r in net.reactions if r.has_product("H2")]

# Multiple species
water_rxns = [r for r in net.reactions if r.has_any_species(["H2O", "OH"])]
```

### By Number of Reactants/Products

```python
# Unimolecular reactions (1 reactant)
unimolecular = [r for r in net.reactions if len(r.reactants) == 1]

# Bimolecular reactions (2 reactants)
bimolecular = [r for r in net.reactions if len(r.reactants) == 2]

# Reactions with single product
simple_products = [r for r in net.reactions if len(r.products) == 1]
```

## Reaction Analysis

### Conservation Checks

Check mass and charge conservation:

```python
# Check individual reaction
rxn = net.reactions[0]
if not rxn.check_mass():
    print(f"Mass not conserved: {rxn.verbatim}")

if not rxn.check_charge():
    print(f"Charge not conserved: {rxn.verbatim}")

# Check all reactions
errors = []
for i, rxn in enumerate(net.reactions):
    if not rxn.check_mass():
        errors.append(f"Reaction {i}: mass error - {rxn.verbatim}")
    if not rxn.check_charge():
        errors.append(f"Reaction {i}: charge error - {rxn.verbatim}")

if errors:
    print(f"Found {len(errors)} conservation errors")
else:
    print("All reactions pass conservation checks")
```

### Reaction Statistics

```python
from collections import Counter

# Count reaction types
types = Counter(r.guess_type() for r in net.reactions)
print("Reaction type distribution:")
for rtype, count in types.items():
    print(f"  {rtype}: {count}")

# Count by number of reactants
n_reactants = Counter(len(r.reactants) for r in net.reactions)
print("\nReactant count:")
for n, count in sorted(n_reactants.items()):
    print(f"  {n} reactants: {count} reactions")

# Count by number of products
n_products = Counter(len(r.products) for r in net.reactions)
print("\nProduct count:")
for n, count in sorted(n_products.items()):
    print(f"  {n} products: {count} reactions")
```

### Find Duplicate Reactions

```python
# Find identical reactions
duplicates = []
for i, r1 in enumerate(net.reactions):
    for r2 in net.reactions[i+1:]:
        if r1.is_same(r2):
            duplicates.append((i, r1.verbatim))

if duplicates:
    print(f"Found {len(duplicates)} duplicate reactions")
    for idx, rxn_str in duplicates[:5]:
        print(f"  {idx}: {rxn_str}")
```

### Find Isomer Versions

```python
# Find reactions with same composition but different species names
isomers = []
for i, r1 in enumerate(net.reactions):
    for j, r2 in enumerate(net.reactions[i+1:], start=i+1):
        if r1.is_isomer_version(r2):
            isomers.append((i, j, r1.verbatim, r2.verbatim))

if isomers:
    print(f"Found {len(isomers)} isomer pairs")
    for i, j, v1, v2 in isomers[:3]:
        print(f"  {i}: {v1}")
        print(f"  {j}: {v2}")
```

## String Representations

### Human-Readable Format

```python
# Get verbatim string
equation = rxn.get_verbatim()
print(equation)  # "H + H -> H2"

# Print directly (uses __str__)
print(rxn)  # Same as above

# Representation (uses __repr__)
print(repr(rxn))  # "Reaction(H + H -> H2, tmin=None, tmax=None, dE=0.0)"
```

### LaTeX Format

```python
# Get LaTeX equation
latex = rxn.get_latex()
print(latex)  # "${\rm H} + {\rm H} \to {\rm H_{2}}$"

# Use in Jupyter notebooks
from IPython.display import display, Latex
for rxn in net.reactions[:5]:
    display(Latex(rxn.get_latex()))
```

### Serialized Forms

```python
# Serialize using species names
ser = rxn.serialize()
print(ser)  # "H_H__H2" (reactants__products)

# Serialize using atomic composition
ser_exp = rxn.serialize_exploded()
print(ser_exp)  # "H/H__H/H" (sorted elements)
```

## Code Generation

### Generate Rate Expressions

```python
# Generate Python code
for rxn in net.reactions[:3]:
    py_code = rxn.get_code(lang="python")
    print(f"{rxn.verbatim}: {py_code}")

# Generate C++ code
for rxn in net.reactions[:3]:
    cpp_code = rxn.get_code(lang="cxx")
    print(f"{rxn.verbatim}: {cpp_code}")

# Generate Fortran code
for rxn in net.reactions[:3]:
    f_code = rxn.get_code(lang="fortran")
    print(f"{rxn.verbatim}: {f_code}")
```

Supported languages:

- `"python"` - Python
- `"c"` - C
- `"cxx"` - C++
- `"fortran"` - Fortran
- `"rust"` - Rust
- `"julia"` - Julia
- `"r"` - R

### Generate Flux Expressions

```python
# Generate flux expression for ODE system
for i, rxn in enumerate(net.reactions[:3]):
    flux = rxn.get_flux_expression(
        idx=i,
        rate_variable="k",
        species_variable="y",
        brackets="[]"
    )
    print(f"flux[{i}] = {flux}")
    # Output: "flux[0] = k[0] * y[idx_h] * y[idx_h]"

# Custom bracket style
flux = rxn.get_flux_expression(
    idx=0,
    rate_variable="rates",
    species_variable="conc",
    brackets="()",
    idx_prefix="n_"
)
```

### Symbolic Manipulation

```python
import sympy

# Get sympy expression
rate_expr = rxn.get_sympy()

# Symbolic differentiation
tgas = sympy.Symbol('tgas')
derivative = sympy.diff(rate_expr, tgas)
print(f"drate/dT = {derivative}")

# Evaluate numerically
rate_func = sympy.lambdify(tgas, rate_expr, "numpy")
import numpy as np
temps = np.logspace(1, 4, 100)
rates = rate_func(temps)
```

## Visualization

### Plot Rate vs Temperature

```python
import matplotlib.pyplot as plt

# Plot single reaction
rxn = net.reactions[0]
rxn.plot()

# Plot multiple reactions on same axis
fig, ax = plt.subplots(figsize=(10, 6))
for rxn in net.reactions[:5]:
    rxn.plot(ax=ax)
plt.legend([r.verbatim for r in net.reactions[:5]])
plt.title("Reaction Rates vs Temperature")
plt.show()
```

### Plot Cross Sections

For photochemical reactions with cross-section data:

```python
# Find photochemical reactions with cross sections
photo_rxns = [r for r in net.reactions if r.xsecs_dict is not None]

if photo_rxns:
    # Plot in eV (default)
    photo_rxns[0].plot_xsecs()

    # Plot as wavelength in nanometers
    photo_rxns[0].plot_xsecs(energy_unit="nm")

    # Plot in micrometers with linear scales
    photo_rxns[0].plot_xsecs(
        energy_unit="um",
        energy_log=False,
        xsecs_log=False
    )

    # Compare multiple reactions
    fig, ax = plt.subplots()
    for rxn in photo_rxns[:3]:
        rxn.plot_xsecs(ax=ax, energy_unit="nm")
    plt.legend([r.verbatim for r in photo_rxns[:3]])
    plt.show()
```

Energy unit options: `"eV"`, `"erg"`, `"nm"`, `"um"` (or `"micron"`)

## Common Patterns

### Formation/Destruction Analysis

```python
def analyze_species(net, species_name):
    """Analyze formation and destruction of a species."""
    formation = [r for r in net.reactions if r.has_product(species_name)]
    destruction = [r for r in net.reactions if r.has_reactant(species_name)]

    print(f"\n{species_name} Chemistry:")
    print(f"  Formation reactions: {len(formation)}")
    print(f"  Destruction reactions: {len(destruction)}")
    print(f"  Ratio: {len(formation)/len(destruction):.2f}")

    print("\nMain formation pathways:")
    for rxn in formation[:5]:
        print(f"  {rxn.verbatim}")

    print("\nMain destruction pathways:")
    for rxn in destruction[:5]:
        print(f"  {rxn.verbatim}")

# Example usage
analyze_species(net, "H2O")
analyze_species(net, "CO")
```

### Export Reaction List

```python
# Export to text file
with open("reactions.txt", "w") as f:
    for i, rxn in enumerate(net.reactions):
        f.write(f"{i}: {rxn.verbatim}\n")
        f.write(f"   Type: {rxn.guess_type()}\n")
        f.write(f"   Rate: {rxn.rate}\n")
        f.write(f"   T range: {rxn.tmin} - {rxn.tmax} K\n")
        f.write("\n")

# Export to CSV
import csv
with open("reactions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Index", "Reaction", "Type", "N_Reactants", "N_Products"])
    for i, rxn in enumerate(net.reactions):
        writer.writerow([
            i,
            rxn.verbatim,
            rxn.guess_type(),
            len(rxn.reactants),
            len(rxn.products)
        ])
```

### Filter by Multiple Criteria

```python
# Complex filtering
selected = []
for rxn in net.reactions:
    # Must involve H2
    if not rxn.has_any_species("H2"):
        continue

    # Must be thermal (not photo)
    if rxn.guess_type() != "unknown":
        continue

    # Must have temperature range defined
    if rxn.tmin is None or rxn.tmax is None:
        continue

    # Must conserve mass and charge
    if not (rxn.check_mass() and rxn.check_charge()):
        continue

    selected.append(rxn)

print(f"Selected {len(selected)} reactions matching all criteria")
```

## See Also

- [Working with Species](species.md) - Chemical species
- [Loading Networks](loading-networks.md) - Network file formats
- [Code Generation](code-generation.md) - Building simulation code
- [API Reference: Reaction](../api/reaction.md) - Complete API documentation

## Notes

- Reactions are created by loading network files, not by direct instantiation
- Mass conservation allows for electron mass tolerance (9.1093837e-28)
- Charge conservation must be exact
- Rate expressions are stored as sympy expressions
- Cross-section data is only available for photochemical reactions
- Temperature ranges are optional and used primarily for plotting and codegen

---

**Next:** Learn about [Code Generation](code-generation.md).
