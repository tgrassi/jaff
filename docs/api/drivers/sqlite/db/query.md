---
tags:
    - Api
---

# query

`#!python query(query)`

Executes a raw SQL query and returns all results.

**Parameters**

**query** : _str_
: SQL query string.

**Returns**

_list_
: Results as `sqlite3.Row` objects.

**Raises**

_RuntimeError_
: On invalid SQL.
