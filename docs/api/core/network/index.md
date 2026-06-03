---
tags:
    - Api
    - Network
---

# Network

`jaff.core.network.Network`

The `Network` class is the most important class in JAFF. It reads a reaction network file, auto-detects its format, validates mass and charge conservation, and assembles the full species and reaction catalogues along with stoichiometry matrices. It also handles optional radiation transport, photochemistry cross-sections, and auxiliary function files.

## Constructor

`#!python Network(fname, errors=False, label=None, funcfile=None, replace_nH=True, rad_bands=[], rad_powerlaw_index=0, rad_energy_density=False, c=constants.cgs.c)`

**Parameters**

**fname** : _str or Path_
: Path to network file. Supported formats: KIDA, UDFA, PRIZMO, KROME, UCLCHEM, a combination of the above and the `.jaff` file (Refer to [to_jaff](to_jaff.md) for more details).

**errors** : _bool, optional_
: Exit on validation errors. Default `False`.

**label** : _str or None, optional_
: Network identifier. Defaults to the file stem.

**funcfile** : _str, Path, or None, optional_
: Path to .jfunc auxiliary functions file. `None` auto-searches; `"none"` skips.

**replace_nH** : _bool, optional_
: Replace nH/nHe symbols with species density sums. Default `True`.

**rad_bands** : _list, optional_
: Radiation band boundaries enabling radiation transport. Default `[]`.

**rad_powerlaw_index** : _int or float, optional_
: Spectral power-law index. Default `0`.

**rad_energy_density** : _bool, optional_
: Interpret radiation as energy density. Default `False`.

**c** : _float, optional_
: Speed of light in CGS. Default `constants.cgs.c`.

**Raises**

_FileNotFoundError_
: If `fname` does not exist.

## Attributes

| Attribute         | Type                | Description                                                                                  |
| ----------------- | ------------------- | -------------------------------------------------------------------------------------------- |
| `label`           | `str`               | Human-readable network identifier; defaults to the source file stem                          |
| `file_name`       | `Path`              | Resolved absolute path to the source network file                                            |
| `species`         | `Species`           | Ordered catalogue of all species in the network                                              |
| `reactions`       | `Reactions`         | Ordered catalogue of all reactions in the network                                            |
| `elements`        | `Elements`          | Element catalogue derived from all species; used for composition matrices                    |
| `reactant_matrix` | `ndarray`           | Shape (n_reactions, n_species) stoichiometry matrix for reactants                            |
| `product_matrix`  | `ndarray`           | Shape (n_reactions, n_species) stoichiometry matrix for products                             |
| `mass_dict`       | `dict`              | Mapping from element symbol to mass properties, used for conservation checks                 |
| `dEdt_chem`       | `sympy.Basic`       | Total chemical heating/cooling rate (erg cm⁻³ s⁻¹), accumulated over all reactions           |
| `dEdt_other`      | `sympy.Basic`       | Additional heating/cooling rate from the `heatingcoolingrate` auxiliary function, if present |
| `dRad_dt_extra`   | `sympy.Basic`       | Extra radiation moment source terms from `@function` definitions                             |
| `radiation`       | `Radiation or None` | Radiation field object; `None` when no radiation bands are specified                         |
