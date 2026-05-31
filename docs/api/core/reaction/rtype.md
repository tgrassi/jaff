---
tags:
    - Api
    - Reaction
---

# rtype

`#!python rtype()`

Classifies this reaction by inspecting its rate expression and stores the result in `self.metadata["type"]`.

Classification rules (evaluated in order):

| Type | Condition |
|------|-----------|
| `"photo"` | Rate is or contains a `photorates(...)` function call |
| `"cosmic_ray"` | Rate contains the free symbol `crate` |
| `"photo_av"` | Rate contains the free symbol `av` |
| `"3_body"` | Rate contains the free symbol `ntot` |
| `"unknown"` | None of the above match |

**Returns**

_str_
: One of `"photo"`, `"cosmic_ray"`, `"photo_av"`, `"3_body"`, or `"unknown"`.
