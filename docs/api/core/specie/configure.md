---
tags:
    - Api
    - Species
---

# configure

`#!python configure(mass_dict)`

Class-level method. Sets the mass dictionary used by all `Specie` instances and propagates it to `Elements`. Called automatically by `Network.__init__`.

**Parameters**

**mass_dict** : _dict_
: Mapping from element symbol to `ElementProps`.
