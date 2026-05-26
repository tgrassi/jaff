---
tags:
    - Api
    - Elements
---

# Elements

`jaff.core.elements.Elements`

Sorted, deduplicated `Catalogue` of elements derived from a species list. Also a flyweight: instances with the same sorted species set are reused. The internal order follows alphabetical sort on element symbol, which fixes the row order of the composition matrices (`truth_matrix`, `density_matrix`).

## Constructor

`#!python Elements(species)`

**Parameters**

**species** : _Specie, list[Specie], str, or list[str]_
: Species to analyze. Strings are auto-converted to `Specie`.

## Attributes

| Attribute | Type           | Description                      |
| --------- | -------------- | -------------------------------- |
| `species` | `list[Specie]` | Species provided at construction |
| `count`   | `int`          | Number of unique elements found  |
