---
tags:
    - Api
    - Reaction
---

# elements

`elements`

Cached property. Builds and returns an `Elements` catalogue covering every chemical element present in either the reactants or the products. The result is cached after the first access so repeated calls do not repeat the parsing work.

**Returns**

_Elements_
: `Elements` catalogue of all unique chemical elements that appear across the reaction's reactants and products.
