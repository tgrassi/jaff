---
tags:
    - Api
    - Elements
---

# from_symbol

`#!python from_symbol(symbol)`

Looks up an element in the JAFF mass dictionary by its periodic-table symbol (case-sensitive) and returns the corresponding `Element` flyweight.

**Parameters**

**symbol** : _str_
: Periodic-table symbol (case-sensitive), e.g. `"H"`, `"He"`, `"C"`.

**Returns**

_Element_
: The `Element` flyweight for the requested element.
