from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


class Db:
    def __init__(self, db_path: Path | str):
        if not isinstance(db_path, (str, Path)):
            raise ValueError("Database path must be a string or pathlib.Path object")

        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        self.table_obj: Table

        if isinstance(db_path, str):
            db_path = Path(db_path)

        self.db_path = db_path

    def connect(self) -> None:
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def close(self) -> None:
        self.__verify_cursor_instance()
        assert self.cursor is not None
        assert self.connection is not None

        self.cursor.close()
        self.connection.close()

    def delete(self) -> None:
        self.db_path.unlink()

    def get_tables(self) -> list[Any]:
        self.__verify_cursor_instance()
        assert self.cursor is not None

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        return self.cursor.fetchall()

    def get_table_names(self) -> list[Any]:
        self.__verify_cursor_instance()
        assert self.cursor is not None

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        return [row[0] for row in self.cursor.fetchall()]

    def table(self, name):
        self.__verify_cursor_instance()
        assert self.cursor is not None
        assert self.connection is not None

        self.table_obj = Table(name, self.connection, self.cursor)

        return self.table_obj

    def table_from_dataframe(self, name: str, df: pd.DataFrame) -> Table:
        self.__verify_cursor_instance()
        assert self.cursor is not None
        assert self.connection is not None

        # index name needs to be set in the dataframe
        index_col = df.index.name or "index"
        columns = ", ".join(f"{col} TEXT" for col in df.columns)

        self.connection.execute(f"""
            CREATE TABLE IF NOT EXISTS {name} (
                {index_col} TEXT PRIMARY KEY,
                {columns}
            )
        """)
        df.to_sql(name=name, con=self.connection, if_exists="replace", index=True)

        return Table(name, self.connection, self.cursor)

    def table_from_csv(self, name: str, file: Path, delimiter: str) -> Table:
        df: pd.DataFrame = pd.read_csv(file, sep=delimiter, index_col=0)

        return self.table_from_dataframe(name, df)

    def query(self, query: str) -> list[Any]:
        try:
            self.__verify_cursor_instance()
            assert self.cursor is not None

            self.cursor.execute(query)
        except sqlite3.Error:
            raise RuntimeError(f"Invalid query: {query}")

        return self.cursor.fetchall()

    def __enter__(self):
        self.connect()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        info = (
            "JAFF SQLite database object\n"
            f"Path: {self.db_path}\n"
            f"Connection: {self.connection}\n"
            f"Cursor: {self.cursor}"
        )

        return info

    def __str__(self):
        info = "JAFF database object"
        return info

    def __verify_cursor_instance(self):
        if not isinstance(self.cursor, sqlite3.Cursor):
            raise RuntimeError(
                "No cursor object found.\nPlease instantiate the database first."
            )


class Table:
    def __init__(self, name: str, conn: sqlite3.Connection, cur: sqlite3.Cursor):
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
        comm = f"SELECT * FROM sqlite_master WHERE type='table' and name='{name}'"
        if not cur.execute(comm).fetchall():
            raise ValueError(f"Invalid table name: {name}")

        self.name = name
        self.cur = cur
        self.conn = conn

    def all_rows(self, cols: list[str] = ["*"]) -> list[Any]:
        comm = f"SELECT {','.join(cols) if len(cols) > 1 else cols[0]} FROM {self.name}"
        self.cur.execute(comm)

        return self.cur.fetchall()

    def rows(
        self,
        cols: list[str] = ["*"],
        conditions: str = "",
    ) -> list[Any]:
        columns = ",".join(cols) if len(cols) > 1 else cols[0]

        comm = (
            f"SELECT {columns} FROM {self.name} WHERE {conditions}"
            if conditions
            else f"SELECT {columns} FROM {self.name}"
        )
        self.cur.execute(comm)

        return self.cur.fetchall()

    def insert_row(self, values: list[str | float | int]) -> None:
        vals = [
            f"'{value}'" if isinstance(value, str) else f"{value}" for value in values
        ]
        comm = f"INSERT INTO {self.name} VALUES ({','.join(vals)})"

        self.cur.execute(comm)

    def insert_rows(self, rows: list[list[str | float | int]]) -> None:
        for row in rows:
            self.insert_row(row)

    def delete(self) -> None:
        comm = f"DROP TABLE {self.name}"
        self.cur.execute(comm)
        self.conn.commit()


class JaffDb(Db):
    def __init__(self):
        jaff_db_path = Path(__file__).parent.parent / "db" / "jaff.db"
        super().__init__(jaff_db_path)
