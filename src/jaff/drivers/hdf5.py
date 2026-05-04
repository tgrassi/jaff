from pathlib import Path
from typing import Any, cast

import h5py
import numpy as np
import pandas as pd

from ..jaff_types import HDF5Dict


class HDF5:
    def __init__(self, compression: str | None = None):
        self.compression = compression

    def to_dict(self, h5file: h5py.File | Path | str) -> HDF5Dict:
        return HDF5Dict(h5file)

    def from_dict(self, h5file: str | Path, h5dict: dict | HDF5Dict) -> None:
        if not isinstance(h5dict, HDF5Dict):
            h5dict = HDF5Dict(h5dict)
        with h5py.File(h5file, "a") as f:
            self.__resolve_to_h5(f, h5dict)

    def to_csv(self, h5file: str | Path, outdir: str | Path, sep=" ") -> None:
        outdir = Path(outdir)
        if not outdir.exists():
            outdir.mkdir(parents=True)

        h5dict = HDF5Dict(h5file)
        self.__generate_csv(h5dict, outdir, "", sep)

    def __resolve_to_h5(self, h5file: h5py.File, h5dict: dict, path: str = "") -> None:
        for key, val in h5dict.items():
            if key == "_attrs":
                target = h5file[path] if path and path != "/" else h5file
                for a_key, a_val in val.items():
                    target.attrs[a_key] = a_val
                continue

            if isinstance(val, dict) and "_kind" in val:
                dataset_path = f"{path}/{key}".replace("//", "/")
                self.__create_dataset(h5file, dataset_path, val)
                continue

            if isinstance(val, dict):
                sub_path = f"{path}/{key}".replace("//", "/")
                h5file.require_group(sub_path)
                self.__resolve_to_h5(h5file, val, sub_path)

    def __create_dataset(self, file: h5py.File, path: str, props: dict[str, Any]) -> None:
        if path in file:
            del file[path]

        kwargs = {"compression": self.compression}
        kind = props.get("_kind")
        data = props.get("_data")
        dtype_spec = props.get("_dtype")

        if kind == "linear":
            dtype = (
                HDF5Dict._to_np().get(cast(str, dtype_spec))
                if isinstance(dtype_spec, str)
                else None
            )
            ds = file.create_dataset(path, data=data, dtype=dtype, **kwargs)

        elif kind == "compound":
            if isinstance(dtype_spec, dict):
                dtype = np.dtype(
                    [(k, HDF5Dict._to_np()[v]) for k, v in dtype_spec.items()]
                )
                ds = file.create_dataset(path, data=data, dtype=dtype, **kwargs)
            else:
                ds = file.create_dataset(path, data=data, **kwargs)
        else:
            raise ValueError(f"Unknown _kind '{kind}' at {path}")

        if "_attrs" in props and props["_attrs"]:
            for a_key, a_val in props["_attrs"].items():
                ds.attrs[a_key] = a_val

        if props.get("_name") is not None:
            ds.attrs["_name"] = props["_name"]

    def __generate_csv(self, data_dict: dict, outdir: Path, current_path: str, sep: str):
        linear_dfs = []
        for key, val in data_dict.items():
            if key == "_attrs":
                continue

            if isinstance(val, dict):
                if "_kind" in val:
                    if val["_kind"] == "linear":
                        col_name = val.get("_name", key)
                        linear_dfs.append(pd.DataFrame({col_name: val["_data"]}))
                    elif val["_kind"] == "compound":
                        df = pd.DataFrame(val["_data"])
                        filename = val.get("_name", key)
                        df.to_csv(outdir / f"{filename}.csv", index=False, sep=sep)
                else:
                    self.__generate_csv(
                        val, outdir, f"{current_path}/{key}" if current_path else key, sep
                    )

        if linear_dfs:
            group_name = current_path.split("/")[-1] if current_path else "out"
            combined_df = pd.concat(linear_dfs, axis=1)
            combined_df.to_csv(outdir / f"{group_name}.csv", index=False, sep=sep)
