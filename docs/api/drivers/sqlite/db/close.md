---
tags:
    - Api
---

# close

`#!python close()`

Closes the active cursor and the underlying database connection. Call this when you are done with the database to release the file handle. When using `Db` as a context manager, this is called automatically on exit.

**Raises**

_RuntimeError_
: If called before `connect()` — there is no open connection to close.
