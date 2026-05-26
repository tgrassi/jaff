---
tags:
    - Api
    - Species
---

# Specie.\_parse

`#!python _parse(mass_dict)`

Parses `self.name` to populate `exploded`, `mass`, `charge`, and the internal LaTeX string. Called automatically by `__init__`.

Uses a proxy substitution strategy to avoid ambiguous greedy matches when element symbols are substrings of each other (e.g. `"C"` inside `"Ca"`): each element symbol is temporarily replaced by a unique 4-character proxy, the formula is tokenized, then proxies are reversed. Symbols are sorted longest-first so multi-character symbols (e.g. `"He"`) match before single-character ones (e.g. `"H"`).

Numeric stoichiometry coefficients immediately following an element token are expanded into repeated atom entries (e.g. `H2` → `["H", "H"]`). The special coefficient `"x"` is treated as 1 so that wildcard species names are tolerated.

Charge is determined by counting trailing `"+"` and `"-"` characters at the _end_ of the name only (avoids misreading embedded signs). `"e-"` is always assigned charge `−1`.

**Parameters**

**mass_dict** : _dict_
: Mapping from element symbol to property dict (must contain at least the key `"mass"`).
