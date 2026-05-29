---
tags:
    - Api
---

# table_from_csv

`#!python table_from_csv(name, file, delimiter)`

Reads a CSV file into a pandas DataFrame and writes it as a new SQLite table. Column types are inferred automatically: integer columns become `INTEGER`, float columns become `REAL`, and everything else becomes `TEXT`. Any existing table with the same name is dropped and replaced.

**Parameters**

**name** : _str_
: Name for the new table in the database.

**file** : _Path_
: Path to the CSV file to import.

**delimiter** : _str_
: Column delimiter character used in the file, e.g. `","` or `" "`.

**Returns**

_Table_
: A `Table` wrapper for the newly created table, ready for further operations.
