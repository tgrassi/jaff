---
tags:
    - Api
    - Code-generation
---

# get_commons

`#!python get_commons(idx_offset=-1, idx_prefix="", definition_prefix="", assignment_op="", line_end="")`

Generates species index definitions and network-size constants. Produces one assignment per species that maps its formatted index name (`fidx`) to its position in the density array, followed by the total species count (`nspecs`) and reaction count (`nreactions`).

Example output for C++ with two species H and H2:

```cpp
const int idx_H  = 0;
const int idx_H2 = 1;
const int nspecs = 2;
const int nreactions = 5;
```

**Parameters**

**idx_offset** : _int, optional_
: Base index added to each species position. `-1` uses the language default stored in `self.ioff`. Default `-1`.

**idx_prefix** : _str, optional_
: Prefix for index names, e.g. `"idx_"`. Default `""`.

**definition_prefix** : _str, optional_
: Type declaration prefix, e.g. `"const int "`. Default `""`.

**assignment_op** : _str, optional_
: Override assignment operator. Default `""` (language default).

**line_end** : _str, optional_
: Override statement terminator. Default `""` (language default).

**Returns**

_str_
: Code block, e.g.: `const int idx_h2 = 0;\nconst int nspecs = 2;`.
