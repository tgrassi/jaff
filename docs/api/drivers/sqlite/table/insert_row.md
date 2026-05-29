---
tags:
    - Api
---

# insert_row

`#!python insert_row(values)`

Inserts a single row into the table and immediately commits the transaction. Values must be provided for every column, in the same order they were defined when the table was created.

**Parameters**

**values** : _list[str or float or int]_
: One value per column, in column definition order.
