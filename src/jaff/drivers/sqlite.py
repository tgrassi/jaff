"""
SQLite database driver.

This module provides two general-purpose SQLite wrappers (:class:`Db` and
:class:`Table`) and one JAFF-specific convenience subclass (:class:`JaffDb`)
that points at the bundled Verner photoionization cross-section database.

Classes
-------
Db
    Context-manager wrapper around a :class:`sqlite3.Connection`.
Table
    Thin query interface for a single table inside a :class:`Db`.
JaffDb
    Subclass of :class:`Db` pre-configured for the built-in ``jaff.db``
    database (Verner photoionization cross-sections).

Typical usage
-------------
::

    from jaff.drivers import JaffDb

    with JaffDb() as db:
        table = db.table("verner96")
        rows = table.rows(cols=["nion", "ne", "sigma0"], conditions="nion = 1")
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .csv import csv_to_df


class Db:
    """
    Context-manager wrapper around a SQLite database connection.

    Manages connection lifecycle (open/close), provides table enumeration,
    and exposes helpers for constructing :class:`Table` objects and running
    raw SQL queries.

    Parameters
    ----------
    db_path : Path or str
        Path to the ``.db`` SQLite file.  The file must already exist.

    Attributes
    ----------
    connection : sqlite3.Connection or None
        Active database connection; ``None`` before :meth:`connect` is called.
    cursor : sqlite3.Cursor or None
        Active cursor; ``None`` before :meth:`connect` is called.
    db_path : Path
        Resolved path to the database file.

    Raises
    ------
    ValueError
        If *db_path* is not a :class:`str` or :class:`~pathlib.Path`.
    FileNotFoundError
        If *db_path* does not exist on the filesystem.
    """

    def __init__(self, db_path: Path | str):
        """Validate and store the database path without opening a connection.

        Parameters
        ----------
        db_path : Path or str
            Path to the ``.db`` SQLite file.

        Raises
        ------
        ValueError
            If *db_path* is not a :class:`str` or :class:`~pathlib.Path`.
        FileNotFoundError
            If *db_path* does not exist on the filesystem.
        """
        if not isinstance(db_path, (str, Path)):
            raise ValueError("Database path must be a string or pathlib.Path object")

        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        self.table_obj: Table

        if isinstance(db_path, str):
            db_path = Path(db_path)

        if not db_path.exists():
            raise FileNotFoundError(db_path)

        self.db_path = db_path

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """
        Open the database connection and create a cursor.

        Uses :attr:`sqlite3.Row` as the row factory so that column values
        can be accessed by name as well as by index.

        Returns
        -------
        None
        """
        self.connection = sqlite3.connect(self.db_path)
        # Row factory enables dict-like access: row["column_name"]
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def close(self) -> None:
        """
        Close the cursor and the underlying database connection.

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            If called before :meth:`connect`.
        """
        self.__verify_cursor_instance()
        assert self.cursor is not None
        assert self.connection is not None

        self.cursor.close()
        self.connection.close()

    def delete(self) -> None:
        """
        Delete the database file from disk.

        Returns
        -------
        None
        """
        self.db_path.unlink()

    # ------------------------------------------------------------------
    # Table enumeration
    # ------------------------------------------------------------------

    def get_tables(self) -> list[Any]:
        """
        Return all table records from the SQLite master table.

        Returns
        -------
        list[sqlite3.Row]
            Each element is a row from ``sqlite_master`` with ``type='table'``.

        Raises
        ------
        RuntimeError
            If called before :meth:`connect`.
        """
        self.__verify_cursor_instance()
        assert self.cursor is not None

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        return self.cursor.fetchall()

    def get_table_names(self) -> list[str]:
        """
        Return the names of all tables in the database.

        Returns
        -------
        list[str]
            Alphabetically unordered list of table name strings.

        Raises
        ------
        RuntimeError
            If called before :meth:`connect`.
        """
        self.__verify_cursor_instance()
        assert self.cursor is not None

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        return [row[0] for row in self.cursor.fetchall()]

    # ------------------------------------------------------------------
    # Table access
    # ------------------------------------------------------------------

    def table(self, name: str) -> "Table":
        """
        Return a :class:`Table` object for the named table.

        Parameters
        ----------
        name : str
            Name of the table to wrap.

        Returns
        -------
        Table
            Query interface for the named table.

        Raises
        ------
        RuntimeError
            If called before :meth:`connect`.
        ValueError
            If *name* does not correspond to an existing table (delegated
            to the :class:`Table` constructor).
        """
        self.__verify_cursor_instance()
        assert self.cursor is not None
        assert self.connection is not None

        self.table_obj = Table(name, self.connection, self.cursor)

        return self.table_obj

    def table_from_dataframe(self, name: str, df: pd.DataFrame) -> "Table":
        """
        Create a new table from a :class:`pandas.DataFrame` and return it.

        Drops any existing table with the same name, infers SQLite column
        types from the DataFrame dtypes (INTEGER / REAL / TEXT), creates the
        table with a primary-key index column, and populates it via
        :meth:`pandas.DataFrame.to_sql`.

        Parameters
        ----------
        name : str
            Name of the table to create.
        df : pandas.DataFrame
            Source data.  The DataFrame's index becomes the primary key
            (named after ``df.index.name`` or ``"index"`` if unnamed).

        Returns
        -------
        Table
            Query interface for the newly created table.

        Raises
        ------
        RuntimeError
            If called before :meth:`connect`.
        """
        self.__verify_cursor_instance()
        assert self.cursor is not None
        assert self.connection is not None

        # Drop any pre-existing table of the same name.
        self.cursor.execute(f"DROP TABLE IF EXISTS {name}")

        index_col = df.index.name or "index"

        # Map pandas dtypes to the closest SQLite affinity type.
        col_defs = []
        for col_name, dtype in df.dtypes.items():
            if pd.api.types.is_integer_dtype(dtype):
                sql_type = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                sql_type = "REAL"
            else:
                sql_type = "TEXT"
            col_defs.append(f"{col_name} {sql_type}")

        columns_str = ", ".join(col_defs)

        self.connection.execute(f"""
            CREATE TABLE {name} (
                {index_col} TEXT PRIMARY KEY,
                {columns_str}
            )
        """)

        df.to_sql(name=name, con=self.connection, if_exists="append", index=True)

        return Table(name, self.connection, self.cursor)

    def table_from_csv(self, name: str, file: Path, delimiter: str) -> "Table":
        """
        Create a new table from a CSV file and return it.

        Delegates to :meth:`table_from_dataframe` after reading the CSV with
        :func:`~jaff.drivers.csv.csv_to_df`.  The first column of the CSV is
        used as the DataFrame index (and therefore the primary key).

        Parameters
        ----------
        name : str
            Name of the table to create.
        file : Path
            Path to the source CSV file.
        delimiter : str
            Field delimiter character for the CSV file.

        Returns
        -------
        Table
            Query interface for the newly created table.
        """
        return self.table_from_dataframe(
            name, csv_to_df(file, sep=delimiter, index_col=0)
        )

    # ------------------------------------------------------------------
    # Raw query
    # ------------------------------------------------------------------

    def query(self, query: str) -> list[Any]:
        """
        Execute a raw SQL query and return all result rows.

        Parameters
        ----------
        query : str
            Valid SQL query string.

        Returns
        -------
        list[sqlite3.Row]
            All rows returned by the query.

        Raises
        ------
        RuntimeError
            If called before :meth:`connect`, or if the query is invalid.
        """
        try:
            self.__verify_cursor_instance()
            assert self.cursor is not None

            self.cursor.execute(query)
        except sqlite3.Error:
            raise RuntimeError(f"Invalid query: {query}")

        return self.cursor.fetchall()

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "Db":
        """Open the connection and return self for use in a ``with`` block."""
        self.connect()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the connection when exiting a ``with`` block."""
        self.close()

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return detailed string representation of this database wrapper.

        Returns
        -------
        str
            Multi-line string showing path, connection, and cursor state.
        """
        info = (
            "JAFF SQLite database object\n"
            f"Path: {self.db_path}\n"
            f"Connection: {self.connection}\n"
            f"Cursor: {self.cursor}"
        )

        return info

    def __str__(self) -> str:
        """Return a short human-readable description of this database wrapper.

        Returns
        -------
        str
        """
        return "JAFF database object"

    def __verify_cursor_instance(self) -> None:
        """
        Raise if the cursor has not been initialised yet.

        Raises
        ------
        RuntimeError
            If ``self.cursor`` is not a :class:`sqlite3.Cursor` instance.
        """
        if not isinstance(self.cursor, sqlite3.Cursor):
            raise RuntimeError(
                "No cursor object found.\nPlease instantiate the database first."
            )


class Table:
    """
    Query interface for a single table inside a :class:`Db` connection.

    Provides methods to select, insert, and drop rows without writing raw
    SQL for each operation.

    Parameters
    ----------
    name : str
        Name of the table.  Must already exist in the database.
    conn : sqlite3.Connection
        Active database connection (typically obtained from :class:`Db`).
    cur : sqlite3.Cursor
        Active cursor for the connection.

    Raises
    ------
    ValueError
        If *conn* is not a :class:`sqlite3.Connection`, *cur* is not a
        :class:`sqlite3.Cursor`, or *name* does not match any table in the
        database.
    """

    def __init__(
        self, name: str, conn: sqlite3.Connection, cur: sqlite3.Cursor
    ):
        """Validate the connection and cursor, then bind to *name* in the database.

        Parameters
        ----------
        name : str
            Name of the table; must already exist in the database.
        conn : sqlite3.Connection
            Active database connection.
        cur : sqlite3.Cursor
            Active cursor for the connection.

        Raises
        ------
        ValueError
            If *conn* is not a :class:`sqlite3.Connection`, *cur* is not a
            :class:`sqlite3.Cursor`, or *name* does not match any table in the
            database.
        """
        if not isinstance(conn, sqlite3.Connection):
            raise ValueError(
                f"Invalid connection passed: {conn}\n"
                "Connection must be an object of sqlite3.Connection"
            )
        if not isinstance(cur, sqlite3.Cursor):
            raise ValueError(
                f"Invalid cursor passed: {cur}\n"
                "Cursor must be an object of sqlite3.Cursor"
            )
        # Verify the table actually exists in the database.
        comm = f"SELECT * FROM sqlite_master WHERE type='table' and name='{name}'"
        if not cur.execute(comm).fetchall():
            raise ValueError(f"Invalid table name: {name}")

        self.name = name
        self.cur = cur
        self.conn = conn

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def all_rows(self, cols: list[str] = ["*"]) -> list[Any]:
        """
        Fetch every row in the table.

        Parameters
        ----------
        cols : list of str, optional
            Columns to retrieve.  Defaults to all columns (``["*"]``).

        Returns
        -------
        list[sqlite3.Row]
            All rows in the table for the selected columns.
        """
        comm = f"SELECT {','.join(cols) if len(cols) > 1 else cols[0]} FROM {self.name}"
        self.cur.execute(comm)

        return self.cur.fetchall()

    def rows(
        self,
        cols: list[str] = ["*"],
        conditions: str = "",
    ) -> list[Any]:
        """
        Fetch rows that match an optional SQL ``WHERE`` clause.

        Parameters
        ----------
        cols : list of str, optional
            Columns to retrieve.  Defaults to all columns (``["*"]``).
        conditions : str, optional
            SQL ``WHERE`` clause body (without the ``WHERE`` keyword), e.g.
            ``"nion = 1 AND ne < 5"``.  If empty, all rows are returned.

        Returns
        -------
        list[sqlite3.Row]
            Matching rows for the selected columns.
        """
        columns = ",".join(cols) if len(cols) > 1 else cols[0]

        comm = (
            f"SELECT {columns} FROM {self.name} WHERE {conditions}"
            if conditions
            else f"SELECT {columns} FROM {self.name}"
        )
        self.cur.execute(comm)

        return self.cur.fetchall()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def insert_row(self, values: list[str | float | int]) -> None:
        """
        Insert a single row into the table.

        Uses parameterised placeholders to guard against SQL injection.

        Parameters
        ----------
        values : list of str, float, or int
            One value per column, in schema order.

        Returns
        -------
        None
        """
        placeholders = ",".join(["?"] * len(values))
        comm = f"INSERT INTO {self.name} VALUES ({placeholders})"
        self.cur.execute(comm, values)
        self.conn.commit()

    def insert_rows(self, rows: list[list[str | float | int]]) -> None:
        """
        Insert multiple rows into the table.

        Calls :meth:`insert_row` for each row, committing after every
        individual insertion.

        Parameters
        ----------
        rows : list of list
            Each inner list must be a valid argument to :meth:`insert_row`.

        Returns
        -------
        None
        """
        for row in rows:
            self.insert_row(row)

    def delete(self) -> None:
        """
        Drop this table from the database.

        Returns
        -------
        None
        """
        comm = f"DROP TABLE {self.name}"
        self.cur.execute(comm)
        self.conn.commit()


class JaffDb(Db):
    """
    Pre-configured database handle for the bundled JAFF database.

    Points at ``jaff/db/jaff.db``, which contains the Verner (1996)
    photoionization cross-section data used by JAFF's photo-reaction
    processing.  Access the data via :meth:`~Db.table`:

    ::

        with JaffDb() as db:
            table = db.table("verner96")
            rows = table.all_rows()

    Parameters
    ----------
    None
        The database path is resolved automatically from the package
        directory.
    """

    def __init__(self):
        """Initialise the database wrapper pointing at the bundled ``jaff.db`` file.

        The path is resolved automatically relative to the JAFF package
        directory; no arguments are required.
        """
        jaff_db_path = Path(__file__).parent.parent / "db" / "jaff.db"
        super().__init__(jaff_db_path)
