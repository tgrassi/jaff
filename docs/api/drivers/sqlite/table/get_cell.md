---
tags:
    - Api
---

# get_cell

`#!python get_cell(index_col, index_value, col_name)`

Fetches the value of a single cell, located by row and column. The row is identified by the value of its index column (typically the primary key), the column by name.

**Parameters**

**index_col** : _str_
: Name of the index/primary-key column used to locate the row.

**index_value** : _str or float or int_
: Value of `index_col` identifying the target row.

**col_name** : _str_
: Name of the column whose cell is fetched.

**Returns**

_Any_
: The cell value if exactly one row matches; `None` if no row matches; a list of values if multiple rows match `index_value`.

**Raises**

_ValueError_
: If `col_name` does not exist in the table.
