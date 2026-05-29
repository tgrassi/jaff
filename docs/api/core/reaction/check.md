---
tags:
    - Api
    - Reaction
---

# check

`#!python check(errors)`

Validates that the reaction conserves both mass and charge by comparing the summed atomic composition and net charge of reactants against that of products. Violations are always logged as warnings; pass `errors=True` to treat them as fatal and terminate the process.

**Parameters**

**errors** : _bool_
: If `True`, calls `sys.exit` on the first conservation violation instead of only logging a warning.
