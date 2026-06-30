---
tags:
    - Api
    - Reaction
---

# from_serialized

`#!python from_serialized(serialized)`

Look up a reaction by its name-level serialized form.

**Parameters**

**serialized** : _str_
: Canonical form `"<sorted_reactants>__<sorted_products>"`, e.g. `"H.H2O+__H2.OH+"`.

**Returns**

_Reaction_
: The matching reaction.
