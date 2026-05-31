---
tags:
    - Api
    - Network
---

# check_unique_reactions

`#!python check_unique_reactions(errors)`

Detects duplicate reactions (same reactants, products, temperature range, and type) and logs a warning for each.

**Parameters**

**errors** : _bool_
: If `True`, exits when duplicates are found.
