---
tags:
    - Api
    - Species
---

# Specie.serialize

`#!python serialize()`

Produces a canonical string key for this specie by sorting its constituent elements alphabetically and joining them with `"/"`. This normalized form is used for consistent lookups and comparisons regardless of how the species was originally written.

**Returns**

_str_
: The sorted, slash-separated element string. For example, `H2O` → `"H/H/O"`.
