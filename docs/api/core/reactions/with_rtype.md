---
tags:
    - Api
    - Reaction
---

# with_rtype

`#!python with_rtype(rtype)`

Filters the catalogue and returns every reaction whose type label matches *rtype*, preserving their relative catalogue order.

**Parameters**

**rtype** : _str_
: Reaction-type label to match, e.g. `"photo"`, `"cosmic_ray"`. Must be one of the type strings stored in `Reaction.metadata["type"]`.

**Returns**

_Vector\[Reaction\]_
: All reactions of the specified type.
