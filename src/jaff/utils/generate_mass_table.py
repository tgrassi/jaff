from pathlib import Path

import pandas as pd

from jaff.core.logger import JaffLogger
from jaff.drivers.sqlite import JaffDb


def main():
    masses = Path(__file__).parent.parent / "data" / "atom_mass.csv"
    df = pd.read_csv(masses, sep=r"\s+", index_col=0)
    rows = [
        {
            "element": f"{symbol}",
            "name": row["Name"],
            "mass": row["Mass"],
        }
        for symbol, row in df.iterrows()
    ]
    del df
    masses_df = pd.DataFrame(rows).set_index("element")
    table_name = "atomic_masses"

    with JaffDb() as jdb:
        table = jdb.table_from_dataframe(table_name, masses_df)
        logger = JaffLogger().get_logger()
        logger.info(f"'{table_name}' table created in {jdb.db_path}\n")

        print(pd.DataFrame(table.all_rows()))


if __name__ == "__main__":
    main()
