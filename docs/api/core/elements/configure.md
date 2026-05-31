---
tags:
    - Api
    - Elements
---

# configure

`#!python configure(mass_dict)`

Class-level method that replaces the global element mass dictionary used by both `Elements` and `Element` (propagates to `Element.configure`). Call this before constructing any `Specie` or `Elements` objects if you need non-default isotopic masses.

**Parameters**

**mass_dict** : _dict_
: Replacement mass dictionary mapping lowercase element names to masses in grams (CGS), e.g. `{"hydrogen": 1.67e-24, "carbon": 2.0e-23}`.
