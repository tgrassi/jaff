---
tags:
    - User-guide
    - Network
---

# Network

`Network` is the entry point for every JAFF workflow and the hub the other
objects hang off. One constructor call reads a network file, parses it into
typed [`Species`](species.md), [`Reactions`](reactions.md), and
[`Elements`](elements.md) catalogues, rewrites every rate into a common symbolic
form, validates the chemistry, and exposes the symbolic ODE/flux/radiation
expressions that downstream code generation consumes.

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")
```

---

## What loading does

A single `Network(...)` call runs a fixed pipeline. Knowing the phases explains
where every attribute comes from:

1. **Read** — the file is resolved and, if it is a binary `.jaff`, deserialized
   directly; otherwise the text parser auto-detects the format (KROME, PRIZMO,
   UDFA, KIDA, UCLChem, …).
2. **Parse & assemble** — reactions are read one by one. Each new species name
   becomes a [`Specie`](species.md) appended to `net.species`; each line becomes
   a [`Reaction`](reactions.md) appended to `net.reactions`. Any accompanying
   `.jfunc` auxiliary file is loaded here and its custom rates, heating/cooling,
   and radiation terms are wired in.
3. **Standardize symbols** — every rate and energy expression is rewritten so
   that number densities use the common [`nden[i]`](#number-densities-the-nden-representation)
   representation (shorthands like `nh`, `ntot`, `n_X` are expanded).
4. **Validate** — mass/charge conservation, sinks/sources, recombinations,
   isomers, and duplicate reactions are [checked](#validation).
5. **Finalize** — integer [stoichiometry matrices](#key-attributes) are built
   and the unique [`Elements`](elements.md) set is derived from the species.

After this, the network is a fully assembled, queryable model.

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
    c=29979245800.0,
)
```

| Parameter            | Type                  | Default | Description                                                                            |
| -------------------- | --------------------- | ------- | -------------------------------------------------------------------------------------- |
| `fname`              | `str or Path`         | —       | Path to the network file (required); `.jaff` files are loaded as binary                |
| `errors`             | `bool`                | `False` | Treat conservation violations / duplicates as fatal (exit) instead of warning          |
| `label`              | `str or None`         | `None`  | Human-readable network name (defaults to the file stem)                                |
| `funcfile`           | `str or Path or None` | `None`  | Path to a `.jfunc` auxiliary file; auto-detected when `None`; pass `"none"` to skip    |
| `replace_nH`         | `bool`                | `True`  | Expand `nh` / `nhe` shorthand into sums of `nden[i]` over H/He-bearing species         |
| `rad_bands`          | `list`                | `[]`    | Radiation band boundaries; an empty list disables radiation transport                  |
| `rad_powerlaw_index` | `int or float`        | `0`     | Power-law spectral index for the radiation field                                       |
| `rad_energy_density` | `bool`                | `False` | Radiation moments are energy densities (`True`) or photon densities (`False`)          |
| `c`                  | `float`               | `c_cgs` | Speed of light in CGS (cm s⁻¹); override when using rsla in radiation codegen manually |

### Examples

```python
# Minimal load
net = Network("networks/GOW/GOW.jet")

# Strict validation — abort on the first conservation failure
net = Network("networks/GOW/GOW.jet", errors=True)

# Custom label and explicit auxiliary-function file
net = Network(
    "networks/GOW/GOW.jet",
    label="GOW-2017",
    funcfile="networks/GOW/GOW.jfunc",
)

# With radiation bands (needed for photochemistry during code generation)
net = Network(
    "networks/h_photoionization/h_photo.jet",
    rad_bands=[13.6, "inf"],
    rad_energy_density=False,
)
```

---

## Key attributes

| Attribute         | Type              | Description                                                                     |
| ----------------- | ----------------- | ------------------------------------------------------------------------------- |
| `file_name`       | `Path`            | Absolute path to the source file                                                |
| `label`           | `str`             | Network name                                                                    |
| `species`         | `Species`         | Ordered [`Species`](species.md) catalogue                                       |
| `reactions`       | `Reactions`       | Ordered [`Reactions`](reactions.md) catalogue                                   |
| `elements`        | `Elements`        | [`Elements`](elements.md) catalogue derived from the species                    |
| `reactant_matrix` | `np.ndarray`      | Integer stoichiometry, shape `(n_reactions, n_species)` — reactant counts       |
| `product_matrix`  | `np.ndarray`      | Integer stoichiometry, same shape — product counts                              |
| `dEdt_chem`       | `sympy.Basic`     | Symbolic total chemical heating/cooling rate (erg cm⁻³ s⁻¹)                     |
| `dEdt_other`      | `sympy.Basic`     | Extra heating/cooling from a `heatingcoolingrate` aux function (else `0`)       |
| `dRad_dt_extra`   | `sympy.Basic`     | Extra radiation-moment source terms from `@function` aux definitions (else `0`) |
| `radiation`       | `Radiation\|None` | Radiation field object; `None` when no `rad_bands` are configured               |
| `mass_dict`       | `dict`            | Element mass dictionary used to build the species                               |

```python
net = Network("networks/h_photoionization/h_photo.jet")

net.label                   # 'h_photo'
net.species.count           # 3
net.reactions.count         # 2
net.reactant_matrix.shape   # (2, 3)   — 2 reactions × 3 species
```

The three catalogues are the same typed collections
documented on [Species](species.md), [Reactions](reactions.md) and
[Elements](elements.md) — anything there works straight off the network:

```python
net.species.names()                 # ['H', 'H+', 'e-']
net.species.charged("name")         # ['H+', 'e-']
net.reactions.verbatim()            # ['H -> H+ + e-', 'H+ + e- -> H']
net.reactions.photo_reactions()     # [ReactionObject(H -> H+ + e-)]
net.elements.symbols()              # ['H']
```

### Stoichiometry matrices

`reactant_matrix[i, j]` counts how many times species _j_ appears as a reactant
in reaction _i_ (and `product_matrix` likewise for products). Row order is
reaction index; column order is species index.

```python
net.reactant_matrix
# [[1 0 0]      reaction 0: H -> H+ + e-   consumes 1× H (species 0)
#  [0 1 1]]     reaction 1: H+ + e- -> H   consumes 1× H+ and 1× e-

net.product_matrix
# [[0 1 1]
#  [1 0 0]]
```

The net stoichiometry `product_matrix - reactant_matrix` is the change in each
species per reaction — the backbone of the ODE system below.

---

## Number densities: the `nden` representation

Inside JAFF every species number density is a reference into one SymPy
`MatrixSymbol("nden", n_species, 1)`. Species _X_ is `nden[idx_X, 0]`, where the
index is the species' position in `net.species`. This is why rate and ODE
expressions print terms like `nden[1, 0]` rather than a named density — it keeps
the whole network on one indexable vector the code generator can emit as an
array.

During loading (phase 3), convenience shorthands in rate expressions are
expanded into this form:

| Shorthand           | Expands to                                                             |
| ------------------- | ---------------------------------------------------------------------- |
| `ntot`              | sum of `nden[i, 0]` over **all** species                               |
| `nh` / `n_H`        | sum over H-bearing species, **weighted** by atom count                 |
| `nhe` / `n_He`      | sum over He-bearing species, weighted                                  |
| `n_X` (e.g. `n_CO`) | `nden[idx_X, 0]` for that one species (`Xp`→`X+`, `Xm`→`X-`, `X0`→`X`) |
| `ne`, `nh2`, …      | the matching single-species density                                    |

For example, a cosmic-ray ionization rate written with `nh` shorthand comes out
as a weighted `nden` sum (note `2*nden[3, 0]` — H₂ contributes two H atoms):

```python
g = Network("networks/GOW/GOW.jet")
g.reactions.with_rtype("cosmic_ray")[0].rate
# crate*(1.5*nden[0, 0]/(nden[0, 0] + nden[1, 0] + 2*nden[3, 0] + ...) + ...)
```

Pass `replace_nH=False` to keep `nh` / `nhe` as opaque free symbols instead of
expanding them — useful when an external driver supplies those densities
directly.

---

## Symbolic expressions

Once loaded, the network exposes its dynamics as SymPy expressions.

### Species ODEs

`Network.sodes()` returns one expression per species — the net rate of change of
its number density (cm⁻³ s⁻¹), summed over every reaction it takes part in:

<!-- prettier-ignore -->
$$ \frac{dn}{dt} = \sum_{i} (-1)^a f_i \quad \begin{cases} a = 0 & n \text{ is a product of reaction } i \\ a = 1 & n \text{ is a reactant of reaction } i \end{cases} $$

where $f_i$ is the flux of the $i^{\text{th}}$ reaction.

```python
for specie, expr in zip(net.species, net.sodes()):
    print(f"d[{specie}]/dt = {expr}")

# d[H]/dt  = 1.659e-10*nden[1, 0]*nden[2, 0]/tgas**0.7 - photorates(1, 13.6, 1.0e+99)*nden[0, 0]
# d[H+]/dt = -1.659e-10*nden[1, 0]*nden[2, 0]/tgas**0.7 + photorates(1, 13.6, 1.0e+99)*nden[0, 0]
# d[e-]/dt = -1.659e-10*nden[1, 0]*nden[2, 0]/tgas**0.7 + photorates(1, 13.6, 1.0e+99)*nden[0, 0]
```

### Fluxes and radiation moments

```python
net.sfluxes()       # list[Expr] — per-reaction flux  k_i * nden[r1] * nden[r2] ...
net.sradodes(0)     # list[Expr] — radiation moment ODEs (order 0), if rad_bands set
```

A flux is just the reaction rate times its reactant densities; the species ODEs
are signed sums of these. See [`sfluxes`](../../api/core/network/sfluxes.md) and
[`sradodes`](../../api/core/network/sradodes.md) for details.

---

## Validation

JAFF validates the network during loading. With `errors=False` (default) each
problem is logged as a warning; with `errors=True` the process exits on the
first one. The individual checks can also be re-run by hand — each takes an
`errors` flag and **logs** its findings (it returns `None`, it does not return a
list):

```python
net.check_sink_sources(errors=False)     # species never produced, or never consumed
net.check_recombinations(errors=False)   # cations lacking an electron recombination
net.check_isomers(errors=False)          # species sharing one atomic composition
net.check_unique_reactions(errors=False) # duplicate reactions (same species, type, T-range)
```

<!-- prettier-ignore -->
!!! note "The checks report, they don't return"
    These methods write warnings through the logger and return `None`. To act on
    the results programmatically, inspect the catalogues directly (e.g. compare
    `reactant_matrix` / `product_matrix` columns for sinks and sources) rather
    than expecting a returned list.

Mass and charge conservation are validated per reaction at construction time —
see [Reactions](reactions.md#conservation-is-checked-at-construction).

---

## Comparing networks

`compare_reactions` and `compare_species` diff two loaded networks, logging what
is shared and what is unique to each. `verbosity=1` (default) also prints the
full sets:

```python
net2 = Network("networks/GOW/GOW.jet")

net.compare_reactions(net2)             # reactions in one but not the other
net.compare_species(net2, verbosity=0)  # counts only, no per-item listing
```

Comparison is by [serialized form](reactions.md#reaction-identity-two-serialized-forms),
so isomer/duplicate handling is consistent with the rest of JAFF.

---

## Export and caching

### Rate tables

Reaction rates can be tabulated against temperature and written to HDF5 or text
for use by external solvers:

```python
net.to_hdf5("rates.hdf5", T_min=10, T_max=1e4, nT=200, err_tol=1e-3)
net.to_txt("rates.txt", T_min=10, T_max=1e4, nT=200)
net.write_table("rates.hdf5", format="auto")  # general form; format from extension (.hdf5/.hdf/.txt)
```

`err_tol` drives adaptive temperature sampling (set it to `None` for a fixed
grid). See [`to_hdf5`](../../api/core/network/to_hdf5.md) and
[`to_txt`](../../api/core/network/to_txt.md).

### JAFF binary format

`to_jaff` serializes an already-loaded network to a gzip-compressed JSON file
(conventional extension `.jaff`). Re-loading skips parsing and the expensive
SymPy assembly, so it is the recommended cache for large networks:

```python
net = Network("networks/GOW/GOW.jet")
net.to_jaff("gow.jaff")        # save

net2 = Network("gow.jaff")     # reload — same species, reactions, and ODEs
```

<!-- prettier-ignore -->
!!! warning "Networks with undefined functions can't be serialized"
    If any rate contains an undefined SymPy function — most commonly an
    unresolved `photorates(...)` (a photo-reaction loaded without `rad_bands`)
    or a custom `interp(...)` — `to_jaff` raises `ValueError`, because such
    expressions cannot be round-tripped through the JSON schema. Resolve the
    radiation/interpolation first, or keep those networks in their text form.
