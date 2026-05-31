---
tags:
    - Api
---

# table_from_dataframe

`#!python table_from_dataframe(name, df)`

Creates a table from a pandas DataFrame. Drops any existing table with the same name. Column types are inferred: integer → `INTEGER`, float → `REAL`, other → `TEXT`.

**Parameters**

**name** : _str_
: Name to assign to the new table. Any existing table with this name is dropped first.

**df** : _pandas.DataFrame_
: Source data used to populate the new table. Column dtypes determine the SQLite column types: integer columns become `INTEGER`, float columns become `REAL`, and all others become `TEXT`.

**Returns**

_Table_
: Table wrapper for the newly created table.
