---
tags:
    - Api
    - Network
---

# Network

`jaff.core.network.Network`

Loads, parses, and manages a chemical reaction network from file. Auto-detects format, validates mass/charge conservation, and builds species/reaction indices.

## Constructor

`#!python Network(fname, errors=False, label=None, funcfile=None, replace_nH=True, rad_bands=[], rad_powerlaw_index=0, rad_energy_density=False, c=constants.cgs.c)`

**Parameters**

**fname** : _str or Path_
: Path to network file. Supported formats: KIDA, UDFA, PRIZMO, KROME, UCLCHEM, .jaff.

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
| `label`           | `str`               | Network identifier                                                                           |
| `file_name`       | `Path`              | Resolved path to source file                                                                 |
| `species`         | `Species`           | All species in the network                                                                   |
| `reactions`       | `Reactions`         | All reactions                                                                                |
| `elements`        | `Elements`          | Element analyzer                                                                             |
| `reactant_matrix` | `ndarray`           | Shape (n_reactions, n_species) reactant stoichiometry                                        |
| `product_matrix`  | `ndarray`           | Shape (n_reactions, n_species) product stoichiometry                                         |
| `mass_dict`       | `dict`              | Element mass dictionary                                                                      |
| `dEdt_chem`       | `sympy.Basic`       | Total chemical heating/cooling rate (erg cm⁻³ s⁻¹), accumulated over all reactions           |
| `dEdt_other`      | `sympy.Basic`       | Additional heating/cooling rate from the `heatingcoolingrate` auxiliary function, if present |
| `dRad_dt_extra`   | `sympy.Basic`       | Extra radiation moment source terms from `@function` definitions                             |
| `radiation`       | `Radiation or None` | Radiation field object; `None` when no radiation bands are specified                         |
| `photochemistry`  | `Photochemistry`    | Cross-section database used to populate `xsecs_dict` on photo-reactions                      |
