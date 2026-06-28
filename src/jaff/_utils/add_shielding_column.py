"""Add the ``shielding`` column to ``photo_reaction_cross_sections`` in ``jaff.db``.

Adds a single ``TEXT`` column named ``shielding`` to the existing
``photo_reaction_cross_sections`` table.  No default is supplied, so every
existing row receives ``NULL`` for the new column.

The operation is idempotent: if the column already exists the script logs a
message and exits without modifying the table.
"""

from jaff.drivers.sqlite import JaffDb
from jaff.io import JaffLogger

#: Target table and the column to add.
TABLE: str = "photo_reaction_cross_sections"
COLUMN: str = "shielding"
COLUMN_TYPE: str = "TEXT"


def main() -> None:
    logger = JaffLogger().get_logger()

    with JaffDb() as jdb:
        # Guard: skip if the column is already present (idempotent rerun).
        existing = jdb.query(
            f"SELECT 1 FROM pragma_table_info('{TABLE}') WHERE name = '{COLUMN}'"
        )
        if existing:
            logger.info(
                f"'{COLUMN}' column already exists in '{TABLE}'; nothing to do\n"
            )
            return

        table = jdb.table(TABLE)
        table.add_column(COLUMN, COLUMN_TYPE)  # default=None -> existing rows NULL
        logger.info(
            f"'{COLUMN}' column added to '{TABLE}' in {jdb.db_path}\n"
        )


if __name__ == "__main__":
    main()
