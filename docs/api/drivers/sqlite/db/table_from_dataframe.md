---
tags:
    - Api
---

# table_from_dataframe

`#!python table_from_dataframe(name, df)`

Creates a table from a pandas DataFrame. Drops any existing table with the same name. Column types are inferred: integer → `INTEGER`, float → `REAL`, other → `TEXT`.

**Parameters**

**name** : _str_
: New table name.

**df** : _pandas.DataFrame_
: Source data.

**Returns**

_Table_
: Table wrapper for the newly created table.
