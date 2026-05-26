---
tags:
    - Api
    - Elements
---

# Element

`jaff.core.elements.Element`

A chemical element loaded from the JAFF mass dictionary. Instances are flyweights: constructing `Element("H")` twice returns the same object. All fields are populated on first construction; subsequent constructions are no-ops.

## Constructor

`#!python Element(symbol)`

**Parameters**

**symbol** : _str_
: Periodic-table symbol (case-sensitive), e.g. `"H"`, `"He"`. Must exist in the JAFF mass dictionary.

## Attributes

| Attribute     | Type    | Description                                                            |
| ------------- | ------- | ---------------------------------------------------------------------- |
| `symbol`      | `str`   | Periodic-table symbol (e.g. `"H"`, `"He"`)                             |
| `name`        | `str`   | Full element name as stored in the mass dictionary (e.g. `"hydrogen"`) |
| `mass`        | `float` | Mass of the most common isotope in grams (CGS)                         |
| `atomic_mass` | `float` | Standard atomic weight in atomic mass units                            |
| `protons`     | `int`   | Number of protons (atomic number)                                      |
| `neutrons`    | `int`   | Number of neutrons in the most common isotope                          |
| `electrons`   | `int`   | Number of electrons in the neutral atom                                |
