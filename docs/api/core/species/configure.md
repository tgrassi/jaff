---
tags:
    - Api
    - Species
---

# configure

`#!python configure(mass_dict)`

Class-level method. Updates the mass dictionary used by all `Specie` instances by delegating to `Specie.configure`. This is called automatically by `Network.__init__`, so you only need it if you are working with a custom mass table outside of a `Network`.

**Parameters**

**mass_dict** : _dict_
: Element mass dictionary.
