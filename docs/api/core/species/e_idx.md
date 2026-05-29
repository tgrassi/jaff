---
tags:
    - Api
    - Species
---

# e_idx

`#!python e_idx()`

Returns the zero-based catalogue index of the electron species `"e-"`, which is needed when building solver state vectors that place the electron density at a fixed position. Returns `None` when the electron is not present in the network.

**Returns**

_int or None_
: Zero-based index of `"e-"` in the species catalogue, or `None` if the electron is not part of the network.
