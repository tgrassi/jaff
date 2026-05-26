---
tags:
    - Api
---

# table

`#!python table(name)`

Returns a `Table` object for the given table name.

**Parameters**

**name** : _str_
: Table name.

**Returns**

_Table_
: Table wrapper for the specified table.

**Raises**

_RuntimeError_
: If `#!python connect()` has not been called.
