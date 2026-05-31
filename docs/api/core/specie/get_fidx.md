---
tags:
    - Api
    - Species
---

# get_fidx

`#!python get_fidx()`

Returns a safe variable name for this specie, suitable for use in generated code. Since `+` and `-` are not valid in identifiers, they are replaced with `j` and `k` respectively. Electrons (`e-`) are always mapped to `"idx_e"` as a special case.

**Returns**

_str_
: A string identifier prefixed with `"idx_"`. For example: `HCO+` → `"idx_hcoj"`, `H2O+` → `"idx_h2oj"`, `e-` → `"idx_e"`.
