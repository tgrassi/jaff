---
tags:
    - Api
---

# set_cell

`#!python set_cell(index_col, index_value, col_name, value)`

Sets the value of a single cell, located by row and column, then commits. The row is identified by the value of its index column (typically the primary key), the column by name. The Python type of `value` is validated against the column's declared SQLite type before writing.

**Parameters**

**index_col** : _str_
: Name of the index/primary-key column used to locate the row.

**index_value** : _str or float or int_
: Value of `index_col` identifying the target row.

**col_name** : _str_
: Name of the column whose cell is being set.

**value** : _str or float or int or bytes_
: New value for the cell. Its type must match the declared column type: `TEXT` → `str`, `INTEGER` → `int`, `REAL` → `int`/`float`, `BLOB` → `bytes`. `bool` is rejected for `INTEGER`/`REAL` columns.

**Returns**

_None_

**Raises**

_ValueError_
: If `col_name` does not exist in the table.

_TypeError_
: If the type of `value` does not match the column's declared type.
