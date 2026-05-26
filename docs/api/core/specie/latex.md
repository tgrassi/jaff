---
tags:
    - Api
    - Species
---

# Specie.latex

`#!python latex(dollars=False)`

Returns a LaTeX representation of the species name with subscript digits, superscript charges, and `\rm` roman font for element names.

Name suffixes are transformed: `_ORTHO`, `_PARA`, `_META` become `o`, `p`, `m` prefixes respectively; `_DUST` becomes an `ice` suffix; `GRAIN` becomes `g`.

**Parameters**

**dollars** : _bool, optional_
: If `True`, wraps the result in `$...$`. Default `False`.

**Returns**

_str_
: LaTeX string, e.g. `"{\rm H_{2}O}"` for H2O, `"{\rm H_{2}O^{+}}"` for H2O+.
