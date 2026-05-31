---
tags:
    - Api
---

# query

`#!python query(query)`

Executes a raw SQL string against the database and returns all matching rows. Rows are returned as `sqlite3.Row` objects, which support both index-based and column-name-based access (e.g. `row["column_name"]`).

**Parameters**

**query** : _str_
: Any valid SQL query string, e.g. `"SELECT * FROM rates WHERE T > 100"`.

**Returns**

_list_
: All result rows as `sqlite3.Row` objects. Returns an empty list if the query produces no results.

**Raises**

_RuntimeError_
: If `connect()` has not been called, or if the SQL string is invalid.
