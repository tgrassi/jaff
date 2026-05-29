---
tags:
    - Api
    - Reaction
---

# serialized

`#!python serialized()`

Returns the name-level canonical key for every reaction in the catalogue, in catalogue order. These keys are used for duplicate detection and dictionary lookup.

**Returns**

_Vector[str]_
: Name-level canonical keys of the form `"<sorted_reactants>__<sorted_products>"` for each reaction, in the same order as the catalogue.
