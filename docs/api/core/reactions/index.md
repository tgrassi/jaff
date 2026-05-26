---
tags:
    - Api
    - Reaction
---

# Reactions

`jaff.core.reaction.Reactions`

Typed, ordered `Catalogue` of `Reaction` objects with dictionary-style lookup by verbatim string or serialized key, and vector accessors for bulk property retrieval.

## Attributes

**count** : _int_
: Total number of reactions in the collection.

## Constructor

`#!python Reactions(reactions=None)`

**Parameters**

**reactions** : _list[Reaction] or None, optional_
: Initial reactions. Default `None` (empty collection).
