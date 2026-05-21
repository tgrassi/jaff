from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from ..common import HDF_EXTENSIONS


def csv_to_df(file: Path, *args, **kwargs) -> pd.DataFrame:
    if not file.exists():
        raise FileNotFoundError(file)

    return pd.read_csv(file, *args, **kwargs)


def csv_to_hdf5(
    file: str | Path,
    outfile: str | Path,
    group_path: str = "",
    hdf5_key: str = "",
    flatten_columns: list[str] = [],
    as_table: bool = False,
    *args,
    **kwargs,
) -> None:
    if isinstance(file, str):
        file = Path(file)

    if not group_path:
        group_path = ""

    if as_table and flatten_columns:
        raise ValueError("Cannot flatten arrays if data is to be saved as table")

    if not hdf5_key:
        hdf5_key = file.stem

    if not file.exists():
        raise FileNotFoundError(file)

    outfile = Path(outfile) if isinstance(outfile, str) else outfile
    if outfile.suffix.lower() not in HDF_EXTENSIONS:
        outfile = outfile.with_suffix(".hdf5")

    df = csv_to_df(file, *args, **kwargs)

    if as_table:
        df.to_hdf(outfile, key=f"{group_path}/{hdf5_key}", format="table")
        return

    with h5py.File(outfile, "a") as f:
        grp = f.require_group(f"{group_path}/{hdf5_key}")
        if flatten_columns:
            if any(col not in df.columns for col in flatten_columns):
                raise RuntimeError(
                    f"Invalid columns found in flatten_columns argument: {', '.join(flatten_columns)}"
                )
            df = df.sort_values(by=flatten_columns)

        for col in df.columns:
            grp.create_dataset(
                col,
                data=np.unique(df[col].to_numpy())
                if col in flatten_columns
                else df[col].to_numpy(),
            )
