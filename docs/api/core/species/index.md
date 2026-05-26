---
tags:
    - Api
    - Species
---

# Species

`jaff.core.species.Species`

Ordered, name-indexed `Catalogue` of `Specie` objects. Supports look-up by name, by serialized form, and by integer index:

```python
species["H2O"]
species["+/H/H/O"]
species[0]
```

The `ne` parameter on many accessor methods excludes the electron species (`"e-"`), which is often treated separately in network solvers.

## Attributes

**count** : _int_
: Total number of species in the collection.

## Constructor

`#!python Species(species=None, check_length=True)`

**Parameters**

**species** : \_list[Specie] or list[str] or None
: Initial species. Plain strings are converted to `Specie` objects with indices assigned in list order. If `None`, an empty catalogue is created.

**check_length** : _bool, optional_
: If `True` (default), verifies that the list and name-dict have the same length. Set to `False` when constructing from reactants/products that may contain duplicate species.
