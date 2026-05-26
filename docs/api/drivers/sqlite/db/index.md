---
tags:
    - Api
---

# Db

`jaff.drivers.sqlite.Db`

Low-level SQLite connection wrapper. Provides connection management, table creation, and query execution. Supports context manager protocol.

## Constructor

`#!python Db(db_path)`

**Parameters**

**db_path** : *str or Path*
:   Path to SQLite database file. Must exist.

**Raises**

*ValueError*
:   If `db_path` is not a `str` or `Path`.

*FileNotFoundError*
:   If the file does not exist.

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `db_path` | `Path` | Resolved path to database file |
| `connection` | `sqlite3.Connection or None` | Active connection (after `#!python connect()`) |
| `cursor` | `sqlite3.Cursor or None` | Active cursor (after `#!python connect()`) |
