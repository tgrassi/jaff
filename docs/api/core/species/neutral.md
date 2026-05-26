---
tags:
    - Api
    - Species
---

# neutral

`#!python neutral(attr="")`

Returns neutral species or one of their attributes.

**Parameters**

**attr** : _str, optional_
: If given, returns the named attribute of each neutral species instead of the `Specie` object itself.

Supported attributes are: `charge` `elements` `exploded` `fidx` `index` `mass` `name` `serialized`

**Returns**

_Vector[Specie or any]_
: Neutral species, or the specified attribute of each.

**Raises**

_ValueError_
: If _attr_ is not a valid `Specie` attribute name.
