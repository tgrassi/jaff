---
tags:
    - Api
    - Reaction
---

# from_verbatim

`#!python from_verbatim(verbatim, rtype=None)`

Looks up a reaction by its verbatim string, optionally filtering by type.

**Parameters**

**verbatim** : _str_
: Verbatim reaction string to look up.

**rtype** : _str or None, optional_
: If given, only returns the reaction if its type matches.

**Returns**

_Reaction or None_
: The matching reaction, or `None` if not found.
