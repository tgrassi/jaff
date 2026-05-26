---
tags:
    - User-guide
    - Species
icon: lucide/dna
---

# Species

JAFF represents the species catalogue as a `Species` collection that holds individual `Specie` objects. Both are available directly from the loaded network.

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")

# Collection
print(net.species.count)       # 3

# Individual specie
h = net.species["H"]
print(h.name, h.mass, h.charge)   # H  1.008  0
```

---

## `Specie` Attributes

| Attribute | Type    | Description |
| --------- | ------- | ----------- |
| `name`    | `str`   | Species identifier (e.g. `"H2"`, `"CO"`, `"H+"`) |
| `mass`    | `float` | Molecular mass in atomic mass units |
| `charge`  | `int`   | Electric charge (0 = neutral, positive = cation, negative = anion) |
| `index`   | `int`   | Zero-based position in the species array |
| `fidx`    | `str`   | Formatted index string used in code generation |
| `latex`   | `str`   | LaTeX-formatted species name |

```python
specie = net.species["CO"]
print(specie.name)    # CO
print(specie.mass)    # 27.9949
print(specie.charge)  # 0
print(specie.index)   # 2
print(specie.latex)   # {\rm CO}
```

---

## Accessing Species

### By name

```python
co   = net.species["CO"]
hplus = net.species["H+"]
e    = net.species["E"]     # electron
```

### By index

```python
first = net.species[0]
last  = net.species[-1]
```

### Iteration

```python
for specie in net.species:
    print(f"{specie.index:3d}  {specie.name:<12}  {specie.mass:.4f} amu  charge {specie.charge:+d}")
```

### Membership test

```python
if "CO" in net.species:
    print("CO is in the network")
```

---

## `Species` Collection Methods

### Counts

```python
net.species.count          # total number of species
```

### Name lists

```python
net.species.names()                  # list[str] — all names in index order
net.species.normalized_names()       # list[str] — names with explicit +/- sign
```

### Mass and charge arrays

```python
net.species.masses()                 # list[float] — mass of each species (amu)
net.species.charges()                # list[int]   — charge of each species

# Exclude the electron pseudo-species
net.species.masses(ne=True)
net.species.charges(ne=True)
```

### Filtering

```python
# Neutral species
neutral = net.species.neutral()                  # list[Specie]
neutral_names  = net.species.neutral("name")     # list[str]
neutral_masses = net.species.neutral("mass")     # list[float]
neutral_idx    = net.species.neutral("index")    # list[int]

# Charged species (cations and anions)
charged = net.species.charged()                  # list[Specie]
charged_names  = net.species.charged("name")     # list[str]
charged_idx    = net.species.charged("index")    # list[int]

# Charged, excluding the electron (ne=True)
charged_ne = net.species.charged("index", ne=True)
```

### Charge truth masks

```python
# list[int]: 1 if charged, 0 if neutral — same length as species count
truths = net.species.charge_truths()

# Exclude electron
truths_ne = net.species.charge_truths(ne=True)
```

### Electron index

```python
e_idx = net.species.e_idx()   # int — index of the electron species
```

### Elemental composition

```python
# Exploded representation: maps each species to its element counts
exploded = net.species.exploded()
```

### LaTeX names

```python
latex_names = net.species.latex()   # list[str]
```

---

## Common Patterns

### Print a formatted summary

```python
print(f"{'Idx':>4}  {'Name':<12}  {'Mass (amu)':>12}  {'Charge':>7}")
print("-" * 42)
for sp in net.species:
    print(f"{sp.index:>4}  {sp.name:<12}  {sp.mass:>12.4f}  {sp.charge:>+7d}")
```

### Find all ions

```python
ions = [s for s in net.species if s.charge != 0]
print(f"{len(ions)} ions: {[s.name for s in ions]}")
```

### Find hydrogen-bearing species

```python
h_bearing = [s for s in net.species if "H" in s.name]
```

### Mass-sorted list

```python
by_mass = sorted(net.species, key=lambda s: s.mass)
for s in by_mass[:5]:
    print(f"{s.name}: {s.mass:.2f} amu")
```
