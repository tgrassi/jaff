---
tags:
    - Introduction
icon: phosphor/rocket-launch
---

# Quick Start Guide

JAFF does two things: it **loads a chemical reaction network** and lets you
inspect it, and it **generates solver code** from that network in the language
of your choice. This guide is a tour of both — enough to use the tool on a real
network, without the full detail. Every step links to the
[User Guide](../user-guide/working-with-networks/index.md) where the same ground
is covered in depth.

## Load and explore a network

A [`Network`](../user-guide/working-with-networks/network.md) is the backbone of
JAFF — it holds every species and reaction, with all their derived properties.
Load one from a file:

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")

print(f"Label:     {net.label}")
print(f"Species:   {net.species.count}")
print(f"Reactions: {net.reactions.count}")
```

```text
Label:     h_photo
Species:   3
Reactions: 2
```

JAFF reads all the common community formats — KIDA, UDFA, PRIZMO, KROME, and
UCLCHEM — and detects which one a file uses automatically, so you never pass a
format flag. See [Network Formats](../user-guide/designing-networks/network-formats.md).

### Species

`net.species` is a catalogue of every [`Specie`](../user-guide/working-with-networks/species.md);
iterate it to see each one's properties:

```python
for s in net.species:
    print(f"{s.index}: {s.name:<3} mass={s.mass:.5e} g  charge={s.charge:+d}")
```

```text
0: H   mass=1.67377e-24 g  charge=+0
1: H+  mass=1.67377e-24 g  charge=+1
2: e-  mass=9.10938e-28 g  charge=-1
```

<!-- prettier-ignore -->
!!! warning "Mass is in grams (CGS), not amu"
    `s.mass` is the physical mass in grams — `H` is `1.674e-24`, not `1.008`.
    JAFF works in CGS so the value drops straight into rate and energy
    expressions.

### Reactions

`net.reactions` holds every [`Reaction`](../user-guide/working-with-networks/reactions.md);
`verbatim` is the human-readable form and `rtype()` classifies it from the rate
expression (`photo`, `cosmic_ray`, `photo_av`, `3_body`, `unknown`):

```python
for r in net.reactions:
    print(f"{r.verbatim:<16} [{r.rtype()}]")
```

```text
H -> H+ + e-     [photo]
H+ + e- -> H     [unknown]
```

A reaction's `rate` is a **SymPy expression**, not a number — it still carries
the temperature symbol `tgas`, so it can be differentiated and compiled to
source. Photo-reactions instead hold an unevaluated `photorates(...)` call:

```python
net.reactions[0].rate    # photorates(1, 13.6, 1.0e+99)
net.reactions[1].rate    # 1.65941781598291e-10/tgas**0.7
```

### Look up and filter

Indexing a catalogue returns the object directly — no loop needed. Species index
by name; reactions index by position, verbatim string, or
[serialized form](../user-guide/working-with-networks/reactions.md#reaction-identity-two-serialized-forms):

```python
net.species["H"]                  # the H Specie
net.reactions[0]                  # first reaction, by index
net.reactions["H -> H+ + e-"]     # by verbatim string
```

The catalogues filter in bulk. Pick reactions by type, or test which species a
reaction touches:

```python
net.reactions.with_rtype("photo")     # the photo subset
net.reactions.photo_reactions()       # same, dedicated accessor
net.reactions.rtypes()                # ['photo', 'unknown']

rec = net.reactions[1]                # H+ + e- -> H
rec.has_reactant(["H+", "e-"])        # True  — all present
rec.has_product("H")                  # True
```

The [Working with Networks](../user-guide/working-with-networks/index.md) guide
covers lookup, elemental composition, conservation checks, and export in full.

## Inspect the ODE system

A loaded network is also a system of ODEs. `net.sodes()` returns one symbolic
expression per species — the net rate of change of its number density
(cm⁻³ s⁻¹), summed over every reaction it takes part in. Densities print as
`nden[i, 0]`, JAFF's indexed representation of the whole network on one vector:

```python
for specie, expr in zip(net.species, net.sodes()):
    print(f"d[{specie}]/dt = {expr}")
```

```text
d[H]/dt  = 1.659e-10*nden[1, 0]*nden[2, 0]/tgas**0.7 - photorates(1, 13.6, 1.0e+99)*nden[0, 0]
d[H+]/dt = -1.659e-10*nden[1, 0]*nden[2, 0]/tgas**0.7 + photorates(1, 13.6, 1.0e+99)*nden[0, 0]
d[e-]/dt = -1.659e-10*nden[1, 0]*nden[2, 0]/tgas**0.7 + photorates(1, 13.6, 1.0e+99)*nden[0, 0]
```

`net.sfluxes()` gives the per-reaction fluxes (rate × reactant densities) that
these are signed sums of. Because everything is symbolic, JAFF can differentiate
it exactly to build the Jacobian during code generation. See
[Symbolic expressions](../user-guide/working-with-networks/network.md#symbolic-expressions).

## Plot rates and cross-sections

Every `Reaction` can plot itself, using the styled `jaff.plotting.Plotter`
house style and returning the `(fig, ax)` it drew on:

```python
rec = net.reactions[1]               # H+ + e- -> H
rec.plot_rate_coefficient()          # rate coefficient vs temperature (log–log)
```

Photo-reactions carry a cross-section table instead of an analytic rate; plot it
against photon energy:

```python
photo = net.reactions[0]             # H -> H+ + e-
photo.plot_xsecs()                              # all processes, overlay, eV vs Mb
photo.plot_xsecs(processes="photo_ionization")  # one process only
photo.plot_xsecs(energy_unit="nm", xsec_unit="cm^2")  # wavelength + cm² axes
photo.plot_xsecs(save=True, filename="h_xsec.pdf")    # write to disk
```

`plot_xsecs` is a no-op on non-photo reactions. See
[`plot_rate_coefficient`](../api/core/reaction/plot_rate_coefficient.md) and
[`plot_xsecs`](../api/core/reaction/plot_xsecs.md).

## Generate code

Code generation is primarily **template-driven**: JAFF expands ordinary source files that
contain `$JAFF` directives into network-specific code. The fastest way to see it
work is a **built-in template** — a ready-made collection you don't have to
write — run through the [`jaffgen`](../user-guide/code-generation/jaffgen.md) CLI:

```bash
jaffgen \
    --network  networks/h_photoionization/h_photo.jet \
    --template fortran_dlsodes \
    --lang     fortran \
    --outdir   generated/
```

```text
INFO     Network loaded successfully!
INFO     Successfully generated files
```

`generated/` now holds a complete, buildable Fortran solver:

```text
commons.f90  fluxes.f90  ode.f90  reactions.f90  main.f90  Makefile
opkda1.f     opkda2.f    opkdmain.f
```

<!-- prettier-ignore -->
!!! note "Why `--lang`?"
    This collection bundles non-source files (a `Makefile`) whose language can't
    be inferred from an extension. `--lang` supplies the fallback. See
    [jaffgen](../user-guide/code-generation/jaffgen.md) for the other built-in
    templates and input options.

### Write your own template

A template is **real source code** in any supported language (C, C++, Fortran,
Python, Rust, Julia, R). The engine reads it line by line: every line is copied
**verbatim**, except `$JAFF` directive blocks, which are expanded against the
network. A directive is recognised only when a line starts with the language's
comment token (`//`, `#`, `!`, …) immediately followed by `$JAFF`, and it runs
until a matching `$JAFF END`.

Two directives cover most needs:

- **`SUB`** substitutes scalar values (`$nspec$`, `$nreact$`, `$label$`, …);
- **`REPEAT`** iterates a collection — with `idx` in the variable list it emits
  one line per item, filling `$token$` placeholders from each item.

```cpp
// rates.cpp — a template
// $JAFF SUB nreact
const int NREACT = $nreact$;
// $JAFF END

void compute_rates(double* k, double T) {
    // $JAFF REPEAT idx, rate IN rates
    k[$idx$] = $rate$;
    // $JAFF END
}
```

Run it against the network:

```bash
jaffgen --network networks/h_photoionization/h_photo.jet --files rates.cpp
```

The expanded file lands in `generated/`, keeping its name. `SUB` swapped the
count; `REPEAT` looped the body once per rate (and emitted the right array
syntax for the language — `k[0]` in C++, `k(1)` in Fortran):

```cpp
const int NREACT = 2;

void compute_rates(double* k, double T) {
    k[0] = photorates(0, …);
    k[1] = …;
}
```

Other collections work the same way — `odes`, `jacobian`, `species`,
`specie_charges`, and more — and a `REPLACE` modifier rewrites the output to
match your own symbol names. The full set of commands (`SUB`, `REPEAT`, `GET`,
`HAS`, `REDUCE`), every collection, and CSE are in the
[Template Syntax](../user-guide/code-generation/template-syntax.md) reference.
The [`Builder`](../user-guide/advanced-code-generation/builder.md) API does the
same generation from Python when the template syntax is insufficient.

## From the terminal

[`jaffx`](../user-guide/working-with-networks/jaffx.md) is a thin CLI around
`Network` for quick inspection and rate-table export — no code generation. Every
subcommand loads a network and calls one method:

```bash
jaffx get num-species --network networks/h_photoionization/h_photo.jet
```

```text
INFO     Total number of species: 3
```

Rate coefficients can be tabulated against temperature and written to HDF5 or
text for an external solver, from the CLI or from Python:

```bash
jaffx export hdf5 --network networks/GOW/GOW.jet --file rates.hdf5 \
    --tmin 10 --tmax 1e4 --nT 200 --err-tol 1e-3
```

```python
net = Network("networks/GOW/GOW.jet")
net.to_hdf5("rates.hdf5", T_min=10, T_max=1e4, nT=200, err_tol=1e-3)
```

`to_jaff` (CLI: `jaffx export jaff`) serializes the whole parsed network to a
compressed `.jaff` file; reloading it skips parsing and the expensive SymPy
assembly, so it is the recommended cache for large networks:

```python
net.to_jaff("gow.jaff")        # save
Network("gow.jaff")            # reload — same species, reactions, and ODEs
```

See [Export and caching](../user-guide/working-with-networks/network.md#export-and-caching).

## Next steps

1. **Concepts** — [Basic Concepts](concepts.md) explains chemical networks and the JAFF model.
2. **Working with Networks** — [inspect, filter, and export](../user-guide/working-with-networks/index.md) loaded networks.
3. **Code Generation** — the [template directive language](../user-guide/code-generation/template-syntax.md) and the [`jaffgen`](../user-guide/code-generation/jaffgen.md) CLI.
4. **API Reference** — the complete [API documentation](../api/index.md).

## Example networks

JAFF ships with several networks to experiment with:

- `networks/demos` — small test networks
- `networks/h_photoionization` — hydrogen photo-ionization (used above)
- `networks/COthin` — CO chemistry
- `networks/GOW` — the Gong–Ostriker–Wolfire network
