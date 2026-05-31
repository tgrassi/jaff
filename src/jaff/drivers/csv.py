"""
CSV file driver utilities.

This module provides thin convenience wrappers around :func:`pandas.read_csv`
and :mod:`h5py` for reading CSV files and converting their contents to HDF5
format.

Functions
---------
csv_to_df
    Read a CSV file and return it as a :class:`pandas.DataFrame`.
csv_to_hdf5
    Read a CSV file and write its contents to an HDF5 file.
"""

from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from ..common import HDF_EXTENSIONS


def csv_to_df(file: Path, *args, **kwargs) -> pd.DataFrame:
    """
    Read a CSV file and return it as a :class:`pandas.DataFrame`.

    A thin wrapper around :func:`pandas.read_csv` that validates existence
    before delegating.

    Parameters
    ----------
    file : Path
        Path to the CSV file to read.
    *args
        Positional arguments forwarded to :func:`pandas.read_csv`.
    **kwargs
        Keyword arguments forwarded to :func:`pandas.read_csv`.

    Returns
    -------
    pandas.DataFrame
        Contents of the CSV file.

    Raises
    ------
    FileNotFoundError
        If *file* does not exist on the filesystem.
    """
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
    """
    Convert a CSV file to HDF5 format.

    Reads *file* with :func:`csv_to_df` and writes the result to *outfile*
    (appending if the HDF5 file already exists).  Supports three storage
    modes:

    * **Default** – Each DataFrame column is stored as a 1-D dataset inside
      an HDF5 group at ``<group_path>/<hdf5_key>``.
    * **Table** – The DataFrame is stored as a PyTables-compatible HDF5 table
      via :meth:`pandas.DataFrame.to_hdf`.  Incompatible with
      *flatten_columns*.
    * **Flatten** – Specified columns are deduplicated with
      :func:`numpy.unique` before storage; useful for storing the unique
      values of a coordinate axis alongside the full data.

    Parameters
    ----------
    file : str or Path
        Path to the source CSV file.
    outfile : str or Path
        Path to the output HDF5 file.  If the suffix is not a recognised HDF5
        extension it is replaced with ``.hdf5``.
    group_path : str, optional
        Parent HDF5 group path under which *hdf5_key* is created.
        Defaults to the root group (``""`` becomes ``""``).
    hdf5_key : str, optional
        Name of the HDF5 group/dataset key.  Defaults to the stem of *file*.
    flatten_columns : list of str, optional
        Column names whose values should be stored as the unique-sorted set of
        values (via :func:`numpy.unique`) rather than the raw array.
    as_table : bool, optional
        If ``True``, write the DataFrame as a PyTables-compatible HDF5 table.
        Cannot be combined with *flatten_columns*.
    *args
        Additional positional arguments forwarded to :func:`csv_to_df`.
    **kwargs
        Additional keyword arguments forwarded to :func:`csv_to_df`.

    Returns
    -------
    None

    Raises
    ------
    FileNotFoundError
        If *file* does not exist.
    ValueError
        If both *as_table* and *flatten_columns* are specified.
    RuntimeError
        If any name in *flatten_columns* is not a column in the DataFrame.
    """
    if isinstance(file, str):
        file = Path(file)

    if not group_path:
        group_path = ""

    if as_table and flatten_columns:
        raise ValueError("Cannot flatten arrays if data is to be saved as table")

    # Default the HDF5 key to the CSV file stem.
    if not hdf5_key:
        hdf5_key = file.stem

    if not file.exists():
        raise FileNotFoundError(file)

    outfile = Path(outfile) if isinstance(outfile, str) else outfile
    # Ensure the output has a valid HDF5 file extension.
    if outfile.suffix.lower() not in HDF_EXTENSIONS:
        outfile = outfile.with_suffix(".hdf5")

    df = csv_to_df(file, *args, **kwargs)

    if as_table:
        # PyTables table format — lets pandas store with full column metadata.
        df.to_hdf(outfile, key=f"{group_path}/{hdf5_key}", format="table")
        return

    # Open in append mode so existing groups/datasets are preserved.
    with h5py.File(outfile, "a") as f:
        grp = f.require_group(f"{group_path}/{hdf5_key}")
        if flatten_columns:
            # Validate that every requested flatten column actually exists.
            if any(col not in df.columns for col in flatten_columns):
                raise RuntimeError(
                    f"Invalid columns found in flatten_columns argument: {', '.join(flatten_columns)}"
                )
            # Sort the DataFrame by the flattened coordinate columns so that
            # numpy.unique returns a contiguous, ordered coordinate axis.
            df = df.sort_values(by=flatten_columns)

        for col in df.columns:
            grp.create_dataset(
                col,
                # For flatten columns store only unique values; all others get
                # the full array.
                data=np.unique(df[col].to_numpy())
                if col in flatten_columns
                else df[col].to_numpy(),
            )
