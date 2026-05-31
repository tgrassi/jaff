---
tags:
    - Api
    - Reaction
---

# species

`species`

Cached property. Merges the reactant and product `Species` collections and returns a deduplicated `Species` catalogue. Useful when you need to iterate over all species touched by a reaction without double-counting any that appear on both sides. The result is cached after the first access.

**Returns**

_Species_
: Deduplicated `Species` catalogue containing every species that appears in either the reactants or the products of this reaction.
