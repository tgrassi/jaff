---
tags:
    - Api
---

# Table

`jaff.drivers.sqlite.Table`

Represents a single SQLite table with row-level read/write operations. Obtained via `#!python Db.table()` or `#!python Db.table_from_dataframe()`.

## Constructor

`#!python Table(name, conn, cur)`

**Parameters**

**name** : *str*
:   Table name. Must already exist in the database.

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
| `name` | `str` | Table name |
| `conn` | `sqlite3.Connection` | Database connection |
| `cur` | `sqlite3.Cursor` | Database cursor |
