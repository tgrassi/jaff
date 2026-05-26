---
tags:
    - Api
    - Reaction
---

# get

`#!python get(reaction, rtype=None)`

Look up a reaction by verbatim string or serialized form, with optional type filter.

**Parameters**

**reaction** : _str_
: Verbatim string (e.g. `"H + H2O+ -> H2 + OH+"`) or serialized form (e.g. `"H_H2Oj__H2_OHj"`).

**rtype** : _str or None, optional_
: If given, only returns the reaction if its type matches.

**Returns**

_Reaction or None_
: The matching reaction, or `None` if not found.
