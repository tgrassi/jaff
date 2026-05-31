---
tags:
    - Api
---

# rows

`#!python rows(cols=["*"], conditions="")`

Fetches rows with optional WHERE filtering.

**Parameters**

**cols** : _list\[str\], optional_
: Columns to select. Default `["*"]`.

**conditions** : _str, optional_
: SQL WHERE clause body (without `"WHERE"`). Default `""`.

**Returns**

_list_
: Rows matching the conditions as `sqlite3.Row` objects. Returns all rows when `conditions` is empty.
