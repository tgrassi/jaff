---
tags:
    - Api
    - Species
---

# charged

`#!python charged(attr="", mass=False, ne=False)`

Returns charged species or one of their attributes.

**Parameters**

**attr** : _str, optional_
: If given, returns the named attribute of each charged species instead of the `Specie` object itself.

Supported attributes are: `charge` `elements` `exploded` `fidx` `index` `mass` `name` `serialized`

**ne** : _bool, optional_
: If `True`, excludes the electron species (`"e-"`). Default `False`.

**Returns**

_Vector[Specie]_
: Charged species, or the specified attribute of each.
