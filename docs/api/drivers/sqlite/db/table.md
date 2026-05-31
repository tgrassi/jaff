---
tags:
    - Api
---

# table

`#!python table(name)`

Returns a `Table` wrapper for the named table, bound to the current connection and cursor. The table must already exist in the database; use `table_from_dataframe()` to create a new one from data.

**Parameters**

**name** : _str_
: Name of the table as it exists in the database.

**Returns**

_Table_
: Table wrapper for the specified table.

**Raises**

_RuntimeError_
: If `#!python connect()` has not been called.
