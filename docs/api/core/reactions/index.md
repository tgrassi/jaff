---
tags:
    - Api
    - Reaction
---

# Reactions

`jaff.core.reaction.Reactions`

The `Reactions` class is a typed, ordered `Catalogue` of `Reaction` objects. It supports dictionary-style lookup by verbatim string or serialized key, and provides vector accessors for bulk retrieval of reaction properties.

## Attributes

**count** : _int_
: Total number of reactions in the collection.

## Constructor

`#!python Reactions(reactions=None)`

**Parameters**

**reactions** : _list\[Reaction\] or None, optional_
: Initial reactions. Default `None` (empty collection).
