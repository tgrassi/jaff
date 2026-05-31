---
tags:
    - Api
    - Elements
---

# configure

`#!python configure(mass_dict)`

Class-level method. Sets the mass dictionary used to instantiate `Element` objects. Must be called before creating any `Element` instances if a custom mass table is needed. Calling it after elements have already been registered has no effect on those existing flyweight instances.

**Parameters**

**mass_dict** : _dict_
: Mapping from element symbol to element properties.
