"""Build the ``photo_reaction_cross_sections`` table in ``jaff.db``.

One row per serialized reaction found in the collapsed cross-section HDF5
files (``data/xsecs/leiden.hdf5`` and ``data/xsecs/norad.hdf5``),
keyed by the HDF5 group name (the serialized reaction stem, e.g. ``"CH__C_H"``).

Columns
-------
- ``reaction``          -- PK, serialized reaction / HDF5 group name.
- ``photo_absorption``  -- 1 only for the H2 dissociation ``H2__H_H``, else 0.
- ``photo_dissociation``-- 1 if a ``photodissociation`` dataset exists.
- ``photo_ionization``  -- 1 if the reaction has an ``e-`` product *and* a
  ``photoionization`` dataset exists.
- ``leiden``            -- ``data/xsecs/leiden.hdf5::<group>`` if the
  reaction is in the Leiden file, else NULL.
- ``norad``             -- ``data/xsecs/norad.hdf5::<group>`` if the
  reaction is in the NORAD file, else NULL.
"""

from pathlib import Path

import h5py
import pandas as pd

from jaff.drivers.sqlite import JaffDb
from jaff.io import JaffLogger

#: Reaction stem flagged as photo-absorption (H2 dissociation).
H2_DISSOCIATION: str = "H2__H_H"

#: Package root (``src/jaff``) -- HDF5 paths are stored relative to this.
PKG_ROOT: Path = Path(__file__).parent.parent

#: source name -> collapsed HDF5 file (relative to ``PKG_ROOT``).
XSEC_FILES: dict[str, Path] = {
    "leiden": Path("data") / "xsecs" / "leiden.hdf5",
    "norad": Path("data") / "xsecs" / "norad.hdf5",
}


def read_groups(h5_path: Path) -> dict[str, set[str]]:
    """Map each group name to the set of dataset names it contains."""
    with h5py.File(h5_path, "r") as h5:
        return {name: set(grp.keys()) for name, grp in h5.items()}


def has_electron_product(reaction: str) -> bool:
    """True if the serialized reaction has ``e-`` among its products."""
    _, _, products = reaction.partition("__")
    return "e-" in products.split("_")


def main() -> None:
    sources = {src: read_groups(PKG_ROOT / rel) for src, rel in XSEC_FILES.items()}
    reactions = sorted(set().union(*(g.keys() for g in sources.values())))

    rows = []
    for reaction in reactions:
        datasets = {
            src for src, groups in sources.items() if reaction in groups
        }
        all_datasets = set().union(
            *(sources[src][reaction] for src in datasets)
        )
        rows.append(
            {
                "reaction": reaction,
                "photo_absorption": int(reaction == H2_DISSOCIATION),
                "photo_dissociation": int("photodissociation" in all_datasets),
                "photo_ionization": int(
                    has_electron_product(reaction)
                    and "photoionization" in all_datasets
                ),
                **{
                    src: (
                        f"{XSEC_FILES[src].as_posix()}::{reaction}"
                        if src in datasets
                        else None
                    )
                    for src in XSEC_FILES
                },
            }
        )

    df = pd.DataFrame(rows).set_index("reaction")
    table_name = "photo_reaction_cross_sections"

    with JaffDb() as jdb:
        table = jdb.table_from_dataframe(table_name, df)
        logger = JaffLogger().get_logger()
        logger.info(f"'{table_name}' table created in {jdb.db_path}\n")
        print(pd.DataFrame(table.all_rows()))


if __name__ == "__main__":
    main()
