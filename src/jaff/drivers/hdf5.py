"""
HDF5 file driver.

This module provides :class:`HDF5`, a high-level wrapper around :mod:`h5py`
that converts between JAFF's in-memory :class:`~jaff.types.HDF5Dict`
representation and on-disk HDF5 files, and can also export HDF5 data to CSV.

The :class:`~jaff.types.HDF5Dict` schema
-----------------------------------------
Each leaf in the nested dictionary corresponds to an HDF5 dataset and must
contain at least the following keys:

``_kind``
    ``"linear"`` for a plain 1-D/N-D array; ``"compound"`` for a NumPy
    structured (record) array.
``_data``
    The actual data (NumPy array or compatible).
``_dtype``
    For ``"linear"``: a JAFF dtype string (e.g. ``"f64"``).
    For ``"compound"``: a ``{field_name: dtype_string}`` mapping.
``_attrs``
    Optional ``{attr_name: attr_value}`` dictionary written as HDF5
    dataset attributes.
``_name``
    Optional human-readable column name stored as the ``_name`` HDF5
    attribute.

Non-leaf nodes in the dictionary produce HDF5 groups.  The special key
``_attrs`` at any level writes HDF5 attributes on the parent group/file root.
"""

from pathlib import Path
from typing import Any, cast

import h5py
import numpy as np
import pandas as pd

from ..types import HDF5Dict


class HDF5:
    """
    High-level HDF5 read/write driver backed by :mod:`h5py`.

    Provides methods to convert between :class:`~jaff.types.HDF5Dict` and
    HDF5 files, and to export HDF5 data to CSV.

    Parameters
    ----------
    compression : str or None, optional
        HDF5 compression filter to apply when creating datasets (e.g.
        ``"gzip"``).  ``None`` disables compression.  Defaults to ``None``.
    """

    def __init__(self, compression: str | None = None):
        """Initialise the HDF5 driver with an optional compression filter.

        Parameters
        ----------
        compression : str or None, optional
            HDF5 compression filter (e.g. ``"gzip"``).  ``None`` disables
            compression.  Defaults to ``None``.
        """
        self.compression = compression

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def to_dict(self, h5file: h5py.File | Path | str) -> HDF5Dict:
        """
        Load an HDF5 file into a nested :class:`~jaff.types.HDF5Dict`.

        Parameters
        ----------
        h5file : h5py.File, Path, or str
            An open :class:`h5py.File` or a path to an HDF5 file on disk.

        Returns
        -------
        HDF5Dict
            Nested dictionary representation of the HDF5 file contents.
        """
        return HDF5Dict(h5file)

    def from_dict(self, h5file: str | Path, h5dict: dict | HDF5Dict) -> None:
        """
        Write an :class:`~jaff.types.HDF5Dict` to an HDF5 file.

        Opens (or creates) *h5file* in append mode and recursively resolves
        all datasets and groups from *h5dict*.

        Parameters
        ----------
        h5file : str or Path
            Path to the target HDF5 file.  Created if it does not exist;
            existing files are updated in-place.
        h5dict : dict or HDF5Dict
            Data to write.  Plain ``dict`` objects are automatically converted
            to :class:`~jaff.types.HDF5Dict`.

        Returns
        -------
        None
        """
        if not isinstance(h5dict, HDF5Dict):
            h5dict = HDF5Dict(h5dict)
        with h5py.File(h5file, "a") as f:
            self.__resolve_to_h5(f, h5dict)

    def to_csv(self, h5file: str | Path, outdir: str | Path, sep: str = " ") -> None:
        """
        Export all datasets from an HDF5 file to CSV files in *outdir*.

        ``"linear"`` datasets at the same HDF5 group level are combined into
        a single CSV file named after the group.  ``"compound"`` datasets each
        produce their own file named after the dataset's ``_name`` attribute
        (or its HDF5 key).

        Parameters
        ----------
        h5file : str or Path
            Path to the source HDF5 file.
        outdir : str or Path
            Directory in which CSV files are written.  Created (including
            parents) if it does not exist.
        sep : str, optional
            Column separator character.  Defaults to a single space.

        Returns
        -------
        None
        """
        outdir = Path(outdir)
        if not outdir.exists():
            outdir.mkdir(parents=True)

        h5dict = HDF5Dict(h5file)
        self.__generate_csv(h5dict, outdir, "", sep)

    # ------------------------------------------------------------------
    # HDF5 write helpers
    # ------------------------------------------------------------------

    def __resolve_to_h5(
        self, h5file: h5py.File, h5dict: dict, path: str = ""
    ) -> None:
        """
        Recursively write *h5dict* into an open HDF5 file.

        Handles three kinds of entries:

        * ``_attrs`` key — write as HDF5 attributes on the current group/root.
        * Dict with ``_kind`` — delegate to :meth:`__create_dataset`.
        * Plain dict — create an HDF5 group and recurse.

        Parameters
        ----------
        h5file : h5py.File
            Open HDF5 file handle in write or append mode.
        h5dict : dict
            Current level of the nested dictionary to process.
        path : str, optional
            Current HDF5 group path being processed.  Empty string means root.

        Returns
        -------
        None
        """
        for key, val in h5dict.items():
            # "_attrs" is a metadata key, not a dataset — write its contents
            # as HDF5 attributes on the enclosing group or root object.
            if key == "_attrs":
                target = h5file[path] if path and path != "/" else h5file
                for a_key, a_val in val.items():
                    target.attrs[a_key] = a_val
                continue

            if isinstance(val, dict) and "_kind" in val:
                # Leaf node — resolve the dataset path and delegate.
                dataset_path = f"{path}/{key}".replace("//", "/")
                self.__create_dataset(h5file, dataset_path, val)
                continue

            if isinstance(val, dict):
                # Intermediate node — ensure the group exists and recurse.
                sub_path = f"{path}/{key}".replace("//", "/")
                h5file.require_group(sub_path)
                self.__resolve_to_h5(h5file, val, sub_path)

    def __create_dataset(
        self, file: h5py.File, path: str, props: dict[str, Any]
    ) -> None:
        """
        Create or replace a single HDF5 dataset at *path*.

        Deletes any pre-existing dataset at the same path before creating the
        new one.  Applies the instance's compression filter.  Handles both
        ``"linear"`` (plain array) and ``"compound"`` (structured array) kinds.

        Parameters
        ----------
        file : h5py.File
            Open HDF5 file handle.
        path : str
            Absolute HDF5 path at which the dataset is created.
        props : dict[str, Any]
            Dataset descriptor dictionary with required key ``_kind`` and
            optional keys ``_data``, ``_dtype``, ``_attrs``, ``_name``.

        Raises
        ------
        ValueError
            If ``props["_kind"]`` is not ``"linear"`` or ``"compound"``.

        Returns
        -------
        None
        """
        # Remove any pre-existing dataset at this path to avoid conflicts.
        if path in file:
            del file[path]

        kwargs = {"compression": self.compression}
        kind = props.get("_kind")
        data = props.get("_data")
        dtype_spec = props.get("_dtype")

        if kind == "linear":
            # Map the JAFF dtype string to a NumPy dtype, if provided.
            dtype = (
                HDF5Dict._to_np().get(cast(str, dtype_spec))
                if isinstance(dtype_spec, str)
                else None
            )
            ds = file.create_dataset(path, data=data, dtype=dtype, **kwargs)

        elif kind == "compound":
            if isinstance(dtype_spec, dict):
                # Build a NumPy structured dtype from the field mapping.
                dtype = np.dtype(
                    [(k, HDF5Dict._to_np()[v]) for k, v in dtype_spec.items()]
                )
                ds = file.create_dataset(path, data=data, dtype=dtype, **kwargs)
            else:
                # No explicit dtype spec — let h5py infer from the data.
                ds = file.create_dataset(path, data=data, **kwargs)
        else:
            raise ValueError(f"Unknown _kind '{kind}' at {path}")

        # Write per-dataset attributes.
        if "_attrs" in props and props["_attrs"]:
            for a_key, a_val in props["_attrs"].items():
                ds.attrs[a_key] = a_val

        # Store the human-readable column name as a special HDF5 attribute.
        if props.get("_name") is not None:
            ds.attrs["_name"] = props["_name"]

    # ------------------------------------------------------------------
    # CSV export helper
    # ------------------------------------------------------------------

    def __generate_csv(
        self,
        data_dict: dict,
        outdir: Path,
        current_path: str,
        sep: str,
    ) -> None:
        """
        Recursively traverse *data_dict* and write CSV files.

        ``"linear"`` datasets found at the same group level are collected and
        written together as a single combined CSV file.  ``"compound"``
        datasets each produce an individual file.  Sub-groups trigger
        recursive descent.

        Parameters
        ----------
        data_dict : dict
            Current level of the :class:`~jaff.types.HDF5Dict` tree.
        outdir : Path
            Output directory.
        current_path : str
            Slash-separated path of the current group (used to derive the
            output file stem).
        sep : str
            Column separator character for the CSV files.

        Returns
        -------
        None
        """
        linear_dfs: list[pd.DataFrame] = []
        for key, val in data_dict.items():
            # Skip metadata keys.
            if key == "_attrs":
                continue

            if isinstance(val, dict):
                if "_kind" in val:
                    if val["_kind"] == "linear":
                        # Accumulate linear columns for a combined CSV later.
                        col_name = val.get("_name", key)
                        linear_dfs.append(pd.DataFrame({col_name: val["_data"]}))
                    elif val["_kind"] == "compound":
                        # Each compound dataset becomes its own CSV file.
                        df = pd.DataFrame(val["_data"])
                        filename = val.get("_name", key)
                        df.to_csv(outdir / f"{filename}.csv", index=False, sep=sep)
                else:
                    # Sub-group — recurse with an extended path.
                    self.__generate_csv(
                        val, outdir, f"{current_path}/{key}" if current_path else key, sep
                    )

        # Write all accumulated linear columns as one combined file per group.
        if linear_dfs:
            group_name = current_path.split("/")[-1] if current_path else "out"
            combined_df = pd.concat(linear_dfs, axis=1)
            combined_df.to_csv(outdir / f"{group_name}.csv", index=False, sep=sep)
