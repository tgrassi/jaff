---
tags:
    - Api
    - Species
---

# neutral

`#!python neutral(attr="")`

Filters the catalogue to species with a net charge of zero and returns either the `Specie` objects or a chosen attribute of each. Preserves the relative catalogue order of the surviving species.

**Parameters**

**attr** : _str, optional_
: Name of a `Specie` attribute to extract. If given, returns that attribute value for each neutral species instead of the `Specie` object itself. Leave empty (default) to return the `Specie` objects.

Supported attributes are: `charge` `elements` `exploded` `fidx` `index` `mass` `name` `serialized`

**Returns**

_Vector[Specie or any]_
: Neutral `Specie` objects in catalogue order, or the value of *attr* for each neutral species if *attr* was given.

**Raises**

_ValueError_
: If _attr_ is not a valid `Specie` attribute name.
