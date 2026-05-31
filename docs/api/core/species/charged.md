---
tags:
    - Api
    - Species
---

# charged

`#!python charged(attr="", mass=False, ne=False)`

Filters the catalogue to species with a non-zero net charge and returns either the `Specie` objects or a chosen attribute of each. Preserves the relative catalogue order of the surviving species.

**Parameters**

**attr** : _str, optional_
: Name of a `Specie` attribute to extract. If given, returns that attribute value for each charged species instead of the `Specie` object itself. Leave empty (default) to return the `Specie` objects.

Supported attributes are: `charge` `elements` `exploded` `fidx` `index` `mass` `name` `serialized`

**mass** : _bool, optional_
: If `True`, returns the mass of each charged species. Equivalent to passing `attr="mass"`. Default `False`.

**ne** : _bool, optional_
: If `True`, excludes the electron species (`"e-"`) from the result even though it is charged. Default `False`.

**Returns**

_Vector\[Specie or any\]_
: Charged `Specie` objects in catalogue order, or the value of *attr* for each charged species if *attr* was given.
