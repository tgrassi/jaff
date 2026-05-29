---
tags:
    - Api
---

# Db

`jaff.drivers.sqlite.Db`

A low-level wrapper around a SQLite database connection. It manages the connection lifecycle (opening and closing), enumerates the tables in the database, and provides helpers for constructing `Table` objects and running raw SQL queries. It can be used as a context manager so the connection is opened and closed automatically.

## Constructor

`#!python Db(db_path)`

The constructor only validates and stores the path; the connection is not opened until you call `connect()` (or enter the context manager).

**Parameters**

**db_path** : _str or Path_
: Path to the `.db` SQLite file. The file must already exist, since the driver does not create new databases.

## Attributes

| Attribute    | Type                         | Description                                                             |
| ------------ | ---------------------------- | ----------------------------------------------------------------------- |
| `db_path`    | `Path`                       | Resolved path to the database file                                      |
| `connection` | `sqlite3.Connection or None` | Active database connection; `None` until `#!python connect()` is called |
| `cursor`     | `sqlite3.Cursor or None`     | Active cursor; `None` until `#!python connect()` is called              |
