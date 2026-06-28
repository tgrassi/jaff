---
tags:
    - Api
---

# add_column

`#!python add_column(col_name, col_type="TEXT", default=None)`

Adds a new column to the table via `ALTER TABLE ... ADD COLUMN` and commits. Existing rows receive `default` (or `NULL` when `default` is not given).

**Parameters**

**col_name** : _str_
: Name of the column to add.

**col_type** : _str, optional_
: SQLite column type/affinity (`"TEXT"`, `"INTEGER"`, `"REAL"`, `"BLOB"`). Defaults to `"TEXT"`.

**default** : _str or float or int or None, optional_
: Default value applied to existing rows and used when no value is supplied on insert. When `None` (default), no `DEFAULT` clause is emitted and existing rows receive `NULL`.

**Returns**

_None_
