---
tags:
    - Api
    - Code-generation
---

# get_dedt

`#!python get_dedt(specific_eint=False, norm=0)`

Generates code for the internal energy time derivative (`dE/dt`). An ideal equation of state is assumed for the calculation. Returns the symbolic energy rate `(dEdt_chem + dEdt_other) / den_tot`, rendered as a target-language expression.

**Parameters**

**specific_eint** : _bool, optional_
: Normalise by total density to yield a *specific* internal-energy rate.

    - `False` → `den_tot = 1` (energy-density rate, erg/cm³/s).
    - `True` → divides by total density (selected via `norm`) to give a per-mass or per-particle rate.

    Default `False`.

**norm** : _int, optional_
: Density normalisation convention when `specific_eint=True`. Ignored when `specific_eint=False`.

    - `0` → mass density `Σ m_i · nden[i]` (result in erg/g/s).
    - `1` → number density `Σ nden[i]` (result in erg/particle/s).

    Default `0`. Raises `ValueError` for any other value.

**Returns**

_str_
: Energy-equation code string (single target-language expression, no assignment or line terminator).
