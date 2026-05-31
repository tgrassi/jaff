---
tags:
    - Api
---

# get_table_names

`#!python get_table_names()`

Returns the names of all user-defined tables in the database, queried from the SQLite master table. Unlike `get_tables()`, this returns plain strings rather than raw row objects, making it more convenient for checking table existence or iterating over table names.

**Returns**

_list\[str\]_
: Names of all tables currently in the database.
