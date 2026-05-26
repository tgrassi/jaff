---
tags:
    - User-guide
    - Code-generation
icon: lucide/box
---

# Builder

`Builder` is a high-level orchestrator that generates a complete, runnable solver project from a loaded network in a single call. It locates a named plugin, resolves the corresponding template directory, and delegates all code-generation and file-writing to the plugin's `#!python main()` entry point.

```python
from jaff import Network
from jaff.codegen import Builder

net = Network("networks/demos/demo2.jet")
b = Builder(net)
b.build(template="python_solve_ivp")
```

**Output**

```text
Building network with template: python_solve_ivp
INFO     Preprocessing commons.py   -> examples/commons.py
INFO     Preprocessing rates.py     -> examples/rates.py
INFO     Preprocessing fluxes.py    -> examples/fluxes.py
INFO     Preprocessing ode.py       -> examples/ode.py
INFO     Copying main.py            -> examples/
Network built successfully using template 'python_solve_ivp'.
Output files are located in: /path/to/examples
```

---

## Constructor

```python
Builder(network)
```

| Parameter | Type      | Description |
| --------- | --------- | ----------- |
| `network` | `Network` | Parsed chemical reaction network |

---

## `#!python build()`

```python
b.build(template="python_solve_ivp", output_dir=None)
```

Generates a complete solver project using the specified plugin template.

| Parameter    | Type           | Default              | Description |
| ------------ | -------------- | -------------------- | ----------- |
| `template`   | `str`          | `"python_solve_ivp"` | Name of the plugin template to use |
| `output_dir` | `str` or `None`| `None` (cwd)         | Destination directory for generated files |

**Returns** `str` — absolute path to the output directory.

**Raises** `SystemExit(1)` if the template name is not found; prints available templates.

---

## Available Templates

Plugin templates live in `src/jaff/templates/preprocessor/` and are importable as `jaff.plugins.<name>.plugin`.

| Template | Language | Solver | Generated Files |
| -------- | -------- | ------ | --------------- |
| `python_solve_ivp` | Python | `scipy.integrate.solve_ivp` | `commons.py`, `rates.py`, `fluxes.py`, `ode.py`, `main.py` |
| `fortran_dlsodes` | Fortran 90 | DLSODES (ODEPACK) | Fortran source + driver |
| `kokkos_ode` | C++ / Kokkos | Kokkos ODE | Kokkos-compatible headers + driver |
| `microphysics` | C++ | AMReX Microphysics | AMReX-compatible RHS + Jacobian |

---

## Example: Python Solver

The `python_solve_ivp` template generates a self-contained Python project.

```python
from jaff import Network
from jaff.codegen import Builder
from pathlib import Path

net = Network("networks/GOW/GOW.jet")
b = Builder(net)
output_path = b.build(template="python_solve_ivp", output_dir="generated/")
```

Generated `ode.py` (excerpt):

```python
def ode(t, y, tgas, av):
    k = rates(tgas, av)
    f = fluxes(k, y)

    dydt = [0.0] * nspecs
    dydt[idx_H]  = -flux[0] + flux[2]
    dydt[idx_H2] =  flux[0] - flux[1]
    # ...
    return dydt
```

Generated `main.py` (excerpt):

```python
from scipy.integrate import solve_ivp
from ode import ode, nspecs

y0 = [1e-4] * nspecs
sol = solve_ivp(lambda t, y: ode(t, y, tgas=10.0, av=1.0),
                t_span=(0, 1e13), y0=y0, method="LSODA")
```

---

## Custom Output Directory

```python
b.build(template="python_solve_ivp", output_dir="/tmp/my_network/")
```

If `output_dir` is `None`, files are written to the current working directory.

---

## Adding Custom Templates

Custom templates follow the plugin convention:

1. Create `src/jaff/templates/preprocessor/<name>/` with template files.
2. Create `src/jaff/plugins/<name>/plugin.py` exposing:

```python
def main(network, *, path_template, path_build):
    ...  # preprocess templates and write output files
```

Then call `#!python b.build(template="<name>")`.
