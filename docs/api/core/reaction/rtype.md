---
tags:
    - Api
    - Reaction
---

# rtype

`#!python rtype()`

Returns the reaction type concluded by the network-format parser. The type is no longer inferred from the rate expression — each parser classifies the reaction while reading the file and supplies the type, which is stored in `self.metadata["type"]`.

| Type | Meaning |
|------|---------|
| `"photo"` | Radiation-driven (photodissociation / photoionisation) |
| `"cosmic_ray"` | Cosmic-ray driven |
| `"3_body"` | Three-body reaction |
| `"unknown"` | Unclassified |

**Returns**

_str_
: One of `"photo"`, `"cosmic_ray"`, `"3_body"`, or `"unknown"`.
