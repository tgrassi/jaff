---
tags:
    - Api
    - Reaction
---

# add

`#!python add(reaction)`

Appends a `Reaction` to the catalogue. Duplicate checking is not performed here; call `Network.check_unique_reactions` separately.

**Parameters**

**reaction** : _Reaction_
: The reaction to add.

**Raises**

_ValueError_
: If *reaction* is not a `Reaction` instance.
