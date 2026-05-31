---
tags:
    - Api
    - Reaction
---

# photo_reaction_truths

`#!python photo_reaction_truths()`

Returns a binary membership vector over the full catalogue indicating which reactions are photo-reactions. Useful for Boolean masking in NumPy pipelines.

**Returns**

_Vector\[int\]_
: `1` if the corresponding reaction is a photo-reaction, `0` otherwise. One entry per reaction, in catalogue order.
