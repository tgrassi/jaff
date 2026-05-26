---
tags:
    - User-guide
    - Elements
icon: lucide/circle-dot
---

# Elements

JAFF automatically extracts the unique chemical elements from all species in a network and exposes them through the `Elements` collection. Element objects are flyweights — creating `#!python Element("H")` twice returns the same instance.

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")

print(net.elements.count)          # 2  (H and E)
print(net.elements.symbols())      # ['H', 'E']
```

---

## `Element` Attributes

| Attribute      | Type    | Description |
| -------------- | ------- | ----------- |
| `symbol`       | `str`   | Periodic-table symbol (e.g. `"H"`, `"C"`, `"O"`) |
| `name`         | `str`   | Full element name (e.g. `"hydrogen"`) |
| `mass`         | `float` | Mass of the most common isotope in grams (CGS) |
| `atomic_mass`  | `float` | Standard atomic weight in atomic mass units |
| `protons`      | `int`   | Atomic number |
| `neutrons`     | `int`   | Neutron count of the most common isotope |
| `electrons`    | `int`   | Electron count of the neutral atom |

```python
h = net.elements["H"]
print(h.symbol)       # H
print(h.name)         # hydrogen
print(h.atomic_mass)  # 1.008
print(h.protons)      # 1
```

---

## Accessing Elements

### By symbol

```python
carbon   = net.elements["C"]
hydrogen = net.elements["H"]
```

### By index

```python
first = net.elements[0]
```

### Iteration and membership

```python
for elem in net.elements:
    print(f"{elem.symbol}: {elem.atomic_mass:.3f} amu")

if "C" in net.elements:
    print("Network contains carbon")
```

---

## `Elements` Collection Methods

### Counts and symbols

```python
net.elements.count            # int — number of unique elements
net.elements.symbols()        # list[str]   — element symbols
net.elements.names()          # list[str]   — element full names
net.elements.masses()         # list[float] — isotope masses in grams
net.elements.atomic_masses()  # list[float] — atomic masses in amu
net.elements.protons()        # list[int]
net.elements.neutrons()       # list[int]
net.elements.electrons()      # list[int]
```

### Lookup by name or symbol

```python
h = net.elements.from_symbol("H")    # Element
h = net.elements.from_name("hydrogen")  # Element
```

---

## Composition Matrices

The composition matrices are used internally by JAFF for stoichiometry checking and code generation. Both have shape `(n_species, n_elements)`.

### Truth matrix

Entry `[i, j]` is `1` if species *i* contains element *j*, else `0`.

```python
truth = net.elements.truth_matrix()
# truth[species_idx, element_idx]

# Which species contain carbon?
c_idx = net.elements["C"].index
c_species_mask = truth[:, c_idx]
```

### Density matrix

Entry `[i, j]` is the number of atoms of element *j* in species *i*.

```python
density = net.elements.density_matrix()

# How many H atoms does H2O contain?
h2o_idx = net.species["H2O"].index
h_idx   = net.elements["H"].index
print(density[h2o_idx, h_idx])   # 2
```

---

## Common Patterns

### Print elemental composition of each species

```python
density = net.elements.density_matrix()
elems   = net.elements.symbols()

print(f"{'Species':<12}", "  ".join(f"{e:>4}" for e in elems))
print("-" * (12 + 6 * len(elems)))
for sp in net.species:
    row = density[sp.index]
    counts = "  ".join(f"{int(n):>4}" for n in row)
    print(f"{sp.name:<12}  {counts}")
```

### Find all species containing a given element

```python
def species_with_element(net, symbol):
    truth   = net.elements.truth_matrix()
    e_idx   = net.elements[symbol].index
    return [s for s in net.species if truth[s.index, e_idx]]

carbon_species = species_with_element(net, "C")
print([s.name for s in carbon_species])
```
