from pathlib import Path

import pandas as pd
from sympy import Expr, Piecewise, Symbol, srepr

from jaff.drivers.sqlite import Db


def verner_xsecs(
    sigma0: float,
    E0: float,
    y0: float,
    y1: float,
    yw: float,
    ya: float,
    P: float,
    Emin: float,
    Emax: float,
) -> Expr:
    def F(x, y):
        p1 = (x - 1) * (x - 1) + yw * yw
        p2 = y ** (0.5 * P - 5.5)
        p3 = (1 + (y / ya) ** 0.5) ** (-P)

        return p1 * p2 * p3

    E = Symbol("E")
    x = E / E0 - y0
    y = (x * x + y1 * y1) ** 0.5

    return Piecewise((sigma0 * F(x, y), (E >= Emin) & (E <= Emax)), (0, True))


def main(create_table: bool = False):
    path = Path(__file__).parent.parent / "db" / "jaff.db"
    verner_data = Path(__file__).parent.parent / "data" / "xsecs" / "verner_1996.csv"
    df = pd.read_csv(verner_data, sep=r"\s+", index_col=0)
    rows = [
        {
            "Ion": index,
            "Z": row["Z"],
            "N": row["N"],
            "xsecs": srepr(
                verner_xsecs(
                    sigma0=row["sigma_0(Mb)"],
                    E0=row["E_0(eV)"],
                    y0=row["y_0"],
                    y1=row["y_1"],
                    yw=row["y_w"],
                    ya=row["y_a"],
                    P=row["P"],
                    Emin=row["E_th(eV)"],
                    Emax=row["E_max(eV)"],
                )
            ),
        }
        for index, row in df.iterrows()
    ]
    xsecs_df = pd.DataFrame(rows).set_index("Ion")

    with Db(path) as db:
        # table = db.table("verner_cross_sections")
        # table.delete()
        # print(db.get_tables())
        table = (
            db.table_from_dataframe("verner_cross_sections", xsecs_df)
            if create_table
            else db.table("verner_cross_sections")
        )
        print(pd.DataFrame(table.all_rows()))
        # print(
        #     db.connection.execute("PRAGMA index_list(verner_cross_sections);").fetchall()
        # )


if __name__ == "__main__":
    # main(create_table=True)
    main()
