---
tags:
    - Api
    - Code-generation
---

# dfs

`#!python dfs(reactions, species)`

Depth-first search over the reaction graph to detect connected components. Used internally for CSE pruning and dependency resolution.

**Parameters**

**reactions** : _Reactions_
: Reactions to traverse.

**species** : _Species_
: Species nodes in the graph.

**Returns**

_list[set]_
: List of connected species sets.
