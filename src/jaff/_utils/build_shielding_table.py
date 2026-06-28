"""Build the ``photo_reaction_shielding`` table in ``jaff.db``.

One row per reaction that has shielding data, indexing the shielding handlers
available for it.  Two TEXT columns hold JSON arrays of handler keywords:

- ``global`` -- names of the shielding HDF5 files (``data/shielding/*.hdf5``)
  that contain the reaction as a group, e.g. ``["leiden"]``.  A global handler
  script (``physics/photo_reactions/shielding/<keyword>.py``) builds the HDF5
  path from the reaction key itself.
- ``local``  -- stems of the reaction-specific scripts under
  ``physics/photo_reactions/shielding/<reaction>/*.py`` (lower-cased), e.g.
  ``["db1996", "hg2015"]``.

A keyword is exactly a (lower-cased) file stem, so the TOML ``type`` selects a
handler by name with no stored paths.  Rows are the union of reactions found in
the shielding HDF5 files and the local script folders; reactions absent from
both get no row (``S = 1`` no-op at runtime).

This table is a regenerable index of the filesystem + HDF5 -- rerun after adding
a shielding file or script.  ``reaction`` is the primary key; no foreign key is
declared because a few shielded reactions (e.g. ``HCl+``/``SH+`` ionisation)
legitimately have no cross-section entry.
"""

import json
from pathlib import Path

import h5py
import pandas as pd

from jaff.drivers.sqlite import JaffDb
from jaff.io import JaffLogger

#: Package root (``src/jaff``).
PKG_ROOT: Path = Path(__file__).parent.parent
#: Directory of global (tabulated) shielding HDF5 files.
SHIELDING_DATA_DIR: Path = PKG_ROOT / "data" / "shielding"
#: Directory of shielding handler scripts (global files + per-reaction folders).
SHIELDING_SCRIPT_DIR: Path = PKG_ROOT / "physics" / "photo_reactions" / "shielding"

TABLE: str = "photo_reaction_shielding"


def collect_global() -> dict[str, list[str]]:
    """Map each reaction to the shielding HDF5 stems that contain it."""
    out: dict[str, list[str]] = {}
    for h5_path in sorted(SHIELDING_DATA_DIR.glob("*.hdf5")):
        keyword = h5_path.stem.lower()
        with h5py.File(h5_path, "r") as f:
            for reaction in f:
                out.setdefault(reaction, []).append(keyword)
    return out


def collect_local() -> dict[str, list[str]]:
    """Map each reaction to its per-reaction shielding script stems."""
    out: dict[str, list[str]] = {}
    for folder in sorted(p for p in SHIELDING_SCRIPT_DIR.iterdir() if p.is_dir()):
        if folder.name.startswith("_") or folder.name == "__pycache__":
            continue
        stems = sorted(
            f.stem.lower()
            for f in folder.glob("*.py")
            if not f.name.startswith("_")
        )
        if stems:
            out[folder.name] = stems
    return out


def main() -> None:
    logger = JaffLogger().get_logger()
    global_map = collect_global()
    local_map = collect_local()

    reactions = sorted(set(global_map) | set(local_map))
    df = pd.DataFrame(
        {
            "reaction": reactions,
            "global": [json.dumps(sorted(global_map.get(r, []))) for r in reactions],
            "local": [json.dumps(local_map.get(r, [])) for r in reactions],
        }
    ).set_index("reaction")

    with JaffDb() as jdb:
        table = jdb.table_from_dataframe(TABLE, df)
        logger.info(f"'{TABLE}' table created in {jdb.db_path} ({len(df)} rows)\n")
        print(pd.DataFrame(table.all_rows()))


if __name__ == "__main__":
    main()
