---
tags:
    - Api
    - Elements
---

# Elements

`jaff.core.elements.Elements`

The `Elements` class is a sorted, deduplicated `Catalogue` of chemical elements derived from a set of species. Like `Element`, it is a flyweight: instances built from the same sorted species set are reused. Elements are ordered alphabetically by symbol, which fixes the row order of the composition matrices (`truth_matrix`, `density_matrix`).

## Constructor

`#!python Elements(species)`

**Parameters**

**species** : _Specie, list\[Specie\], str, or list\[str\]_
: Species to analyze. Strings are auto-converted to `Specie`.

## Attributes

| Attribute | Type           | Description                                                               |
| --------- | -------------- | ------------------------------------------------------------------------- |
| `species` | `list[Specie]` | The species provided at construction, stored as a list of `Specie` objects |
| `count`   | `int`          | Number of distinct chemical elements found across all provided species     |
