---
tags:
    - Api
---

# get_tables

`#!python get_tables()`

Queries the SQLite schema and returns one `sqlite3.Row` per table, giving you direct access to the raw metadata columns (e.g. `type`, `name`, `sql`). Prefer `get_table_names()` if you only need the table names.

**Returns**

_list_
: One raw `sqlite3.Row` object per table in the database, in the order returned by the SQLite schema query.
