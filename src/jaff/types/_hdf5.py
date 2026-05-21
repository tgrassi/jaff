from contextlib import nullcontext
from pathlib import Path
from typing import Any

import h5py
import numpy as np


class HDF5Dict(dict):
    def __init__(self, h5obj: h5py.File | Path | str | dict):
        if isinstance(h5obj, dict):
            super().__init__(h5obj)
            return

        if isinstance(h5obj, (str, Path)):
            h5path = Path(h5obj)
            if not h5path.exists():
                raise FileNotFoundError(h5path)

        cm = nullcontext(h5obj) if isinstance(h5obj, h5py.File) else h5py.File(h5obj, "r")
        result = {}

        with cm as f:
            if f.attrs:
                result["_attrs"] = dict(f.attrs)
            f.visititems(lambda name, obj: self.__build_nested_dict(result, name, obj))

        super().__init__(result)

    def flatten(self, d: dict = {}, parent_key: str = "") -> dict:
        if not d:
            d = self

        items = {}
        endpoint_data = {}
        has_endpoint = False

        for k, v in d.items():
            if k.startswith("_"):
                endpoint_data[k] = v
                has_endpoint = True

        if has_endpoint:
            items[parent_key or "/"] = endpoint_data

        for k, v in d.items():
            if not k.startswith("_") and isinstance(v, dict):
                new_key = f"{parent_key}/{k}" if parent_key != "/" else f"/{k}"
                new_key = new_key.replace("//", "/")
                items.update(self.flatten(v, new_key))

        return items

    def nested(self, d: dict = {}) -> dict:
        if not d:
            d = self

        nested_dict = {}
        for path, data in d.items():
            if path == "/":
                nested_dict.update(data)
                continue

            parts = [p for p in path.split("/") if p]
            current = nested_dict
            for part in parts[:-1]:
                current = current.setdefault(part, {})

            if parts:
                leaf = parts[-1]
                if leaf not in current:
                    current[leaf] = {}
                current[leaf].update(data)

        return nested_dict

    def __build_nested_dict(self, root: dict, name: str, obj: h5py.Group | h5py.Dataset):
        parts = name.split("/")
        current = root
        for part in parts[:-1]:
            current = current.setdefault(part, {})

        leaf_key = parts[-1]

        if isinstance(obj, h5py.Dataset):
            attrs = dict(obj.attrs)
            ds_name = attrs.pop("_name", None)
            node = {
                "_kind": "compound" if obj.dtype.fields else "linear",
                "_data": obj[()],
                "_attrs": attrs,
            }
            if ds_name is not None:
                node["_name"] = ds_name
            if obj.dtype.fields:
                node["_dtype"] = {
                    n: self.__decode_dtype(obj.dtype[n]) for n in obj.dtype.names
                }
            else:
                node["_dtype"] = self.__decode_dtype(obj.dtype)

            current[leaf_key] = node
        else:
            group_node = current.setdefault(leaf_key, {})
            if obj.attrs:
                group_node["_attrs"] = dict(obj.attrs)

    def __decode_dtype(self, dtype):
        dt = np.dtype(dtype)
        if dt in self._from_np():
            return self._from_np()[dt]
        return "s" if dt.kind in ("S", "U", "O") else str(dt)

    @staticmethod
    def _to_np() -> dict[str, Any]:
        mapping = {
            "i8": np.int8,
            "i16": np.int16,
            "i32": np.int32,
            "i64": np.int64,
            "u8": np.uint8,
            "u16": np.uint16,
            "u32": np.uint32,
            "u64": np.uint64,
            "f16": np.float16,
            "f32": np.float32,
            "f64": np.float64,
            "c64": np.complex64,
            "c128": np.complex128,
            "b": np.bool_,
            "s": h5py.string_dtype(),
        }

        if hasattr(np, "float128"):
            mapping["f128"] = np.float128

        return mapping

    @staticmethod
    def _from_np():
        return {np.dtype(v): k for k, v in HDF5Dict._to_np().items() if k != "s"}
