---
tags:
    - Api
---

# Table

`jaff.drivers.sqlite.Table`

The `Table` class represents a single SQLite table and provides row-level read/write operations. Instances are obtained via `#!python Db.table()` or `#!python Db.table_from_dataframe()`.

## Constructor

`#!python Table(name, conn, cur)`

**Parameters**

**name** : *str*
:   Name of the table as it exists in the SQLite database. Used to qualify all queries executed through this wrapper.

**conn** : *sqlite3.Connection*
:   Active database connection.

**cur** : *sqlite3.Cursor*
:   Active database cursor.

**Raises**

*ValueError*
:   If the table does not exist or types are invalid.

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the table in the database |
| `conn` | `sqlite3.Connection` | The active database connection shared with the parent `Db` |
| `cur` | `sqlite3.Cursor` | The active cursor used to execute queries on the table |
