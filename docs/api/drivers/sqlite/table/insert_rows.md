---
tags:
    - Api
---

# insert_rows

`#!python insert_rows(rows)`

Inserts multiple rows by calling `insert_row` for each entry. Each row is committed individually. For bulk imports, prefer `Db.table_from_dataframe()` which uses pandas' optimized path.

**Parameters**

**rows** : _list[list[str or float or int]]_
: A list of rows, where each row is a list of column values in column definition order.
