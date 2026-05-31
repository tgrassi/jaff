---
tags:
    - Api
    - Reaction
---

# get_flux_expression

`#!python get_flux_expression(idx=0, rate_variable="k", species_variable="y", brackets="[]", idx_prefix="")`

Returns a string for the flux expression:

<!-- prettier-ignore -->
$$ \text{k} \times \prod_{i=0}^{N} n_i $$

where $k$ is the rate coefficient and $n_i$ are the concentration of the reactants

**Parameters**

**idx** : _int, optional_
: Rate coefficient array index offset. Default `0`.

**rate_variable** : _str, optional_
: Name of the rate coefficient array. Default `"k"`.

**species_variable** : _str, optional_
: Name of the species density array. Default `"y"`.

**brackets** : _str, optional_
: Two-character bracket string, e.g. `"[]"` or `"()"`. Default `"[]"`.

**idx_prefix** : _str, optional_
: Prefix for species index names. Default `""`.

**Returns**

_str_
: e.g. `"k[0] * y[idx_h] * y[idx_o]"`.
