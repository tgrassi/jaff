---
tags:
    - Api
    - Species
---

# charge_truths

`#!python charge_truths(ne=False)`

Returns a binary vector indicating which species are charged.

**Parameters**

**ne** : _bool, optional_
: If `True`, excludes `"e-"`. Default `False`.

**Returns**

_Vector[int]_
: `1` for charged species, `0` for neutral.

**Examples**

```python
s = Species(["H2", "H+", "e-"])
print(s.charge_truths())
print(s.charge_truths(ne=True))
```

Output

```text
[0, 1, 1]
[0, 1]
```
