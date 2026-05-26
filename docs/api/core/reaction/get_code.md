---
tags:
    - Api
    - Reaction
---

# get_code

`#!python get_code(lang="cpp")`

Returns the rate expression as a code string in the target language.

**Parameters**

**lang** : _str, optional_
: Target language: `"python"`, `"c"`, `"cxx"`, `"fortran"`, `"rust"`, `"julia"`, `"r"`. Default `"cpp"`.

**Returns**

_str_
: Rate expression code. Photo-reactions return `"photorates($IDX$, ...)"`.
