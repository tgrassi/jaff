---
tags:
    - Api
---

# all_rows

`#!python all_rows(cols=["*"])`

Fetches all rows, optionally selecting specific columns.

**Parameters**

**cols** : _list[str], optional_
: Column names to select. Default `["*"]` (all columns).

**Returns**

_list_
: All rows as `sqlite3.Row` objects, supporting both index and column-name access.
