---
tags:
    - Api
    - Elements
---

# from_name

`#!python from_name(name)`

Looks up an element in the JAFF mass dictionary by its full lowercase name and returns the corresponding `Element` flyweight.

**Parameters**

**name** : _str_
: Full element name as stored in the mass dictionary (lowercase), e.g. `"hydrogen"`, `"carbon"`.

**Returns**

_Element_
: The `Element` flyweight for the requested element.
