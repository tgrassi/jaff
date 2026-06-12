---
tags:
    - User-guide
    - Reaction
---

# Reactions

When a [`Network`](network.md) is loaded, every line of the network file becomes
a structured object. They are produced by the parser and can be accessed through
`Network.reactions`. This page is about what `Network.reactions` actually
contains and how to use it.

As with [species](species.md), there are **two layers**:

- a single **`Reaction`** — one chemical transformation, carrying its reactants,
  products, symbolic rate, temperature bounds, and energy budget;
- the **`Reactions` Catalogue** — the ordered, doubly-keyed collection that holds
  every `Reaction` in the network and lets you query them in bulk.

`net.reactions` _is_ the Catalogue. Indexing into it hands you one `Reaction`.
The running example throughout is the hydrogen photo-ionization network — two
reactions, one of each interesting kind: a photo-ionization and its inverse
recombination.

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")

net.reactions.count            # 2
net.reactions.verbatim()       # ['H -> H+ + e-', 'H+ + e- -> H']
```

---

## The two layers

A `Reaction` knows about _itself_ — which species go in, which come out, how
fast it proceeds, and how much energy it releases. It does not know its place in
the network or how it couples to other reactions; that context belongs to the
catalogue.

The `Reactions` catalogue knows about _the set_ — ordering (each reaction's
`index`), two ways to look a reaction up, and how to project any per-reaction
attribute into a flat array for the solver and code generator.

```text
net.reactions                       ← the Reactions catalogue (the set)
  ├── net.reactions[0]  → Reaction  ← one transformation (H -> H+ + e-)
  └── net.reactions[1]  → Reaction  ← one transformation (H+ + e- -> H)
```

Everything below follows that seam: the individual reaction first, then the
catalogue, with the symbolic rate and the two notions of "same reaction" as the
ideas to hold onto.

---

## The individual `Reaction`

### The rate is symbolic, not a number

The single most important thing about a `Reaction` is that its `rate` is a
**SymPy expression**, not a float. It is a formula in the gas temperature
`tgas` (and possibly other symbols like `crate`, `av`, `ntot`), frozen at load
time but not yet evaluated.

```python
rec = net.reactions[1]      # H+ + e- -> H  (recombination)
rec.rate                    # 1.65941781598291e-10/tgas**0.7
```

Because the rate is symbolic, a single reaction can be turned into many concrete
forms on demand — differentiated, compiled to six languages, or plotted:

```python
import sympy

rec.get_sympy()                          # 1.65941781598291e-10/tgas**0.7
sympy.diff(rec.get_sympy(), "tgas")      # analytic dk/dT, also symbolic
```

A photo-reaction's rate is instead an unevaluated `photorates(...)` call, which
is what marks it as photochemical (see [reaction types](#reaction-types)):

```python
net.reactions[0].rate       # photorates(1, 13.6, 1.0e+99)
```

<!-- prettier-ignore -->
!!! note "Photo-reactions during code generation"
    Photo reaction rate during code generation are not kept as photorates if radiation is enabled. Actual photorates are calculated as a function of photo number/energy density for each radiation band

### Attributes

| Attribute             | Type            | Description                                                               |
| --------------------- | --------------- | ------------------------------------------------------------------------- |
| `reactants`           | `Species`       | Catalogue of reactant species (may repeat, e.g. for 3-body reactions)     |
| `products`            | `Species`       | Catalogue of product species                                              |
| `rate`                | `sympy.Basic`   | Symbolic rate-coefficient expression (units depend on reaction order)     |
| `tmin`                | `float or None` | Lower temperature bound of rate validity (K); `None` = unbounded          |
| `tmax`                | `float or None` | Upper temperature bound of rate validity (K); `None` = unbounded          |
| `dE`                  | `sympy.Basic`   | Energy released per reaction event (erg), from a `.jfunc` aux function    |
| `dRad`                | `sympy.Basic`   | Radiation energy emission per photon energy (eV) per event                |
| `verbatim`            | `str`           | Human-readable equation `"R1 + R2 -> P1 + P2"`                            |
| `index`               | `int`           | Zero-based position of this reaction inside `net.reactions`               |
| `serialized`          | `str`           | Canonical **name-level** identity (isomer-sensitive)                      |
| `serialized_exploded` | `str`           | Canonical **atom-level** identity (isomer-insensitive)                    |
| `metadata`            | `dict`          | Key/value store; `metadata["type"]` holds the classified reaction type    |
| `custom_rad_rate`     | `bool`          | `True` when the radiation rate came from a `.jfunc`, not cross-sections   |
| `xsecs_dict`          | `XsecsProps or None` | Photo cross-section data: `photon_energy` (eV) plus `photo_absorption`/`photo_ionization`/`photo_dissociation` (cm²); else `None` |

<!-- prettier-ignore -->
!!! tip "`reactants` and `products` are `Species` Catalogues"
    They are not plain name lists — they are full [`Species`](species.md)
    collections, so every per-species accessor works on them
    (`rxn.reactants.names()`, `rxn.products.charges()`, …). The same species may
    appear more than once, so they are built without the length check.

```python
rxn = net.reactions[0]

rxn.verbatim                 # 'H -> H+ + e-'
rxn.reactants.names()        # ['H']
rxn.products.names()         # ['H+', 'e-']
rxn.tmin, rxn.tmax           # (None, None)
rxn.index                    # 0
```

### Conservation is checked at construction

Every `Reaction` validates mass and charge conservation when it is built — a
violation is logged as a warning (or aborts the load when the network is opened
with `errors=True`). You can re-run the checks yourself:

```python
rxn.check_mass()    # True  — mass balances within one electron mass
rxn.check_charge()  # True  — net charge identical on both sides
```

`check_mass` deliberately tolerates a one-electron-mass discrepancy
(`9.109e-28 g`), so an ionization that "loses" an electron still passes.

---

## Reaction identity: two serialized forms

Just as a [`Specie`](species.md) has a canonical `serialized` identity, so does
a reaction — but a reaction has **two**, and the difference is the whole point.

```python
rxn.serialized            # 'H__H+_e-'    ← name-level  (isomer-sensitive)
rxn.serialized_exploded   # 'H__+/H_e-'   ← atom-level  (isomer-insensitive)
```

Both sort the species on each side and join reactants `__` products. They differ
in _what_ they sort:

- **`serialized`** uses species **names**. `HCO+` and `HOC+` are different here.
  This is the form used for `==`, hashing, and the catalogue's serialized
  lookup. Two reactions are equal when their `serialized` strings match.
- **`serialized_exploded`** uses each species' atom-level `serialized` form, so
  isomers collapse together. This is what `is_isomer_version` compares to decide
  whether two reactions are the same chemistry written with different isomer
  names.

```python
net.reactions[0].is_isomer_version(net.reactions[1])   # False
```

`is_isomer_version` returns `True` only when the atom-level forms match _and_ at
least one species name differs — i.e. genuine isomer twins, not identical
reactions.

### Comparing and printing a `Reaction`

A reaction's identity for comparison is its **name-level `serialized` form**.
Equality, ordering, and hashing all reduce to that string — so two reactions
written differently but with the same sorted reactants and products are equal,
regardless of `index`, rate, or temperature bounds:

```python
r0, r1 = net.reactions[0], net.reactions[1]

r0 == r1               # False — different serialized forms
r0 == net.reactions[0] # True  — same reaction

r0 < r1                # compares serialized strings, not index order
sorted([r1, r0])       # [ReactionObject(H+ + e- -> H), ReactionObject(H -> H+ + e-)]
```

<!-- prettier-ignore -->
!!! warning "Ordering is by serialized string, not by index"
    `<` / `>` sort on the `serialized` form, which need not match catalogue
    order. Above, `r1` sorts before `r0` even though its `index` is larger.
    Comparing against a non-`Reaction` (e.g. a string) raises `TypeError`.

Because equality is by `serialized`, reactions can be used in `set`s and as
`dict` keys, and `==` is the basis for the duplicate-reaction check the network
runs at load time.

Printing a reaction gives its human-readable equation; `repr` wraps it:

```python
str(net.reactions[0])    # 'H -> H+ + e-'            ← __str__ is the verbatim
repr(net.reactions[0])   # 'ReactionObject(H -> H+ + e-)'
print(net.reactions[0])  # H -> H+ + e-
```

`str(reaction)` returning the verbatim equation is what lets you drop a
`Reaction` straight into f-strings and log lines.

---

## Reaction types

`rtype()` classifies a reaction by **inspecting its rate expression** — there is
no separate type field in the file. The result is cached in `metadata["type"]`.

| Type           | Trigger in the rate expression    | Example rate                |
| -------------- | --------------------------------- | --------------------------- |
| `"photo"`      | a `photorates(...)` function call | `photorates(1, 13.6, 1e99)` |
| `"cosmic_ray"` | contains the symbol `crate`       | `0.46*crate`                |
| `"photo_av"`   | contains the symbol `av`          | `7.1e-7*exp(-0.5*av)`       |
| `"3_body"`     | contains the symbol `ntot`        | `k0 + k1*ntot`              |
| `"unknown"`    | none of the above                 | `1.66e-10/tgas**0.7`        |

```python
net.reactions[0].rtype()   # 'photo'
net.reactions[1].rtype()   # 'unknown'
net.reactions.rtypes()     # ['photo', 'unknown']
```

### Photo-reactions, a special citizen

Photo-reactions are to `Reactions` what the electron is to `Species` — present
in the catalogue like any other, but special-cased throughout. A photo-reaction
carries a cross-section table instead of an analytic rate:

```python
photo = net.reactions[0]

photo.rate                              # photorates(1, 13.6, 1.0e+99)
photo.xsecs_dict.keys()                 # units, _equations, photon_energy,
                                        #   photo_absorption, photo_ionization,
                                        #   photo_dissociation
len(photo.xsecs_dict["photon_energy"])  # number of grid points (energies in eV)
photo.xsecs_dict["photo_ionization"]    # cross sections in cm^2 (or None)
```

The `photon_energy` grid is in eV and each process array is in cm² (or `None`
when that process has no data for the reaction). The `_equations` sub-dict
carries boolean `pa`/`pi`/`pd` flags marking which processes apply.

The catalogue gives you dedicated ways to pick them out:

```python
net.reactions.photo_reactions()         # Vector[Reaction] — just the photo ones
net.reactions.photo_reaction_truths()   # [1, 0]  — 1 where photo
net.reactions.photo_reaction_indices()  # [0]     — their positions
```

When generating code, and radiation is disabled, a photo-reaction's rate is emitted with an `$IDX$`
placeholder that the code generator fills in with the real array index later:

```python
photo.get_code(lang="cxx")   # 'photorates($IDX$, 13.6000000000000, 1.0e+99)'
```

---

## The `Reactions` catalogue

`net.reactions` is ordered (the order matches every `Reaction.index` and the
stoichiometry matrices) and can be looked up two ways.

### Two ways to find a reaction

```python
net.reactions[0]                  # by index        → Reaction
net.reactions[-1]                 # negative index  → last reaction
net.reactions["H -> H+ + e-"]     # by verbatim string
net.reactions["H__H+_e-"]         # by serialized form
```

The typed helpers do the same with an optional type filter:

```python
net.reactions.from_verbatim("H -> H+ + e-")
net.reactions.from_serialized("H__H+_e-")
net.reactions.get("H -> H+ + e-", rtype="photo")   # None if type mismatches
```

### Iteration and count

`net.reactions.count` is the number of reactions, and the catalogue is sized, so
`len(net.reactions)` returns the same value — `count` is the cached attribute,
`len()` the Pythonic spelling. (The same holds for a single reaction's
`reactants` / `products`, which are `Species` catalogues: `len(rxn.reactants)`
equals `rxn.reactants.count`.)

```python
for rxn in net.reactions:
    print(f"{rxn.index:>3}  {rxn.verbatim:<16}  {rxn.rtype()}")

net.reactions.count   # 2
len(net.reactions)    # 2   — identical
```

### Bulk accessors

Each returns a `Vector` aligned to catalogue order.

| Method                  | Returns                 | h_photo result                       |
| ----------------------- | ----------------------- | ------------------------------------ |
| `verbatim()`            | `Vector[str]`           | `['H -> H+ + e-', 'H+ + e- -> H']`   |
| `rtypes()`              | `Vector[str]`           | `['photo', 'unknown']`               |
| `rates()`               | `Vector[Basic]`         | the two symbolic rate expressions    |
| `reactants()`           | `Vector[Species]`       | one `Species` catalogue per reaction |
| `products()`            | `Vector[Species]`       | one `Species` catalogue per reaction |
| `tmins()` / `tmaxes()`  | `Vector[float or None]` | `[None, None]` / `[None, None]`      |
| `dE()` / `dRad()`       | `Vector[Basic]`         | energy / radiation expressions       |
| `serialized()`          | `Vector[str]`           | `['H__H+_e-', 'H+_e-__H']`           |
| `serialized_exploded()` | `Vector[str]`           | atom-level serialized strings        |

<!-- prettier-ignore -->
!!! warning "`reactants()` / `products()` return `Species`, not name lists"
    Each element is a full [`Species`](species.md) catalogue, not a list of
    strings. Call `.names()` on it if you want the names.

### Filter by type

```python
net.reactions.photo_reactions()              # the photo subset
net.reactions.with_rtype("cosmic_ray")       # cosmic-ray reactions
net.reactions.with_rtype("unknown")          # everything unclassified
```

Note the type keys are `"photo"`, `"cosmic_ray"`, `"photo_av"`, `"3_body"`,
`"unknown"` — there is no `"CR"`.

---

## `Reaction` methods

### Species membership

`has_reactant` / `has_product` test that **all** given species are on that side;
`has_any_species` tests for **any** on either side. Each accepts a name, a
`Specie`, or a list.

```python
rec = net.reactions[1]            # H+ + e- -> H

rec.has_reactant("H+")            # True
rec.has_reactant(["H+", "e-"])    # True  — all present
rec.has_product("H")              # True
rec.has_any_species("e-")         # True  — on either side
```

### String representations

```python
rxn = net.reactions[0]

rxn.verbatim                # 'H -> H+ + e-'   (also rxn.get_verbatim())
rxn.get_latex()             # '${\\rm H}\\,\\to\\,{\\rm H^{+}} + {\\rm e^{-}}$'
rxn.serialize()             # 'H__H+_e-'
rxn.serialize_exploded()    # 'H__+/H_e-'
```

### Code generation

`get_code` renders the rate expression as source for a target language. Supported
keys: `python`, `c`, `cxx`, `fortran`, `rust`, `julia`, `r`.

```python
rec = net.reactions[1]

rec.get_code(lang="python")    # '1.65941781598291e-10*tgas**(-0.7)'
rec.get_code(lang="cxx")       # '...*std::pow(tgas, -0.7...)'
rec.get_code(lang="fortran")   # '1.65941781598291d-10*tgas**(-0.7d0)'
rec.get_code(lang="julia")     # '1.65941781598291e-10 * tgas .^ (-0.7)'
```

`get_flux_expression` builds the reaction flux `k[i] * y[idx_R1] * y[idx_R2]…`
from each reactant's `fidx`, with configurable variable names and brackets:

```python
rec.get_flux_expression(idx=1)
# 'k[1] * y[idx_hj] * y[idx_e]'

rec.get_flux_expression(idx=1, rate_variable="k",
                        species_variable="nden", brackets="()")
# 'k(1) * nden(idx_hj) * nden(idx_e)'
```

### Plotting

Both plotters use the styled `jaff.plotting.Plotter` house style and return the
`(fig, ax)` they drew on, so plots can be composed or saved.

```python
rec.plot_rate_coefficient()         # rate vs temperature (log–log)

photo = net.reactions[0]
photo.plot_xsecs()                              # all processes, overlay, eV vs Mb
photo.plot_xsecs(processes="photo_ionization")  # one process only
photo.plot_xsecs(layout="subplots")             # one stacked panel per process
photo.plot_xsecs(energy_unit="nm", xsec_unit="cm^2")  # wavelength + cm² axes
photo.plot_xsecs(save=True, filename="h_xsec.pdf")    # write to disk
```

`plot_rate_coefficient` spans `[tmin, tmax]`, defaulting to `2.73 K` and `1e6 K`
when a bound is `None`. `plot_xsecs` is a no-op (returns `None`) for non-photo
reactions (those with `xsecs_dict is None`) or when no requested process has
data.

---

## Common patterns

### Conservation audit

```python
bad = [r.verbatim for r in net.reactions
       if not (r.check_mass() and r.check_charge())]

if bad:
    print(f"Conservation failures ({len(bad)}):")
    for v in bad:
        print(f"  {v}")
else:
    print("All reactions conserve mass and charge.")
```

### Formation and destruction pathways

```python
def pathways(net, species_name):
    formed    = [r for r in net.reactions if r.has_product(species_name)]
    destroyed = [r for r in net.reactions if r.has_reactant(species_name)]
    print(f"{species_name}: {len(formed)} formation / {len(destroyed)} destruction")
    for r in formed:
        print(f"  +  {r.verbatim}")
    for r in destroyed:
        print(f"  -  {r.verbatim}")

pathways(net, "H+")
```

### Group reactions by type

```python
from collections import Counter

Counter(net.reactions.rtypes())     # Counter({'photo': 1, 'unknown': 1})
```

### Export to CSV

```python
import csv

with open("reactions.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["index", "reaction", "type", "tmin", "tmax",
                "n_reactants", "n_products"])
    for rxn in net.reactions:
        w.writerow([rxn.index, rxn.verbatim, rxn.rtype(),
                    rxn.tmin, rxn.tmax,
                    len(rxn.reactants), len(rxn.products)])
```
