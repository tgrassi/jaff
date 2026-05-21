import copy
from functools import cached_property
from pathlib import Path
from typing import Any

import pandas as pd

from ..common._helper import CSV_EXTENSIONS, HDF_EXTENSIONS
from ..types import HDF5Dict


class ConfigTable:
    def __init__(self, table_dict: dict[str, Any], file: Path, network_file: Path):
        self.config: dict[str, Any] = table_dict
        self.network_dir = network_file.parent
        self.network_name: Path = Path(network_file.stem)
        if not self.network_name.exists():
            raise RuntimeError(
                f"{self.network_dir} doesn't contain any default data file"
            )

        if "source" not in table_dict:
            raise KeyError(f"source must be specified in {file}")
        self.source_config: dict[str, Any] = self.config["source"]
        self.target_config: dict[str, Any] = self.config.get("target", {})

        self.source_props = {}
        self.target_props = {}
        self.__set_source_props()
        self.__set_target_props()

        self.source_tree: dict[str, Any] | HDF5Dict = self.__get_source_tree()

    def parse(self):
        if self.target_props["type"] == "hdf5":
            return self.__parse_to_hdf5()
        elif self.target_props["type"] == "csv":
            return self.__parse_to_csv()

    def __parse_to_hdf5(self) -> HDF5Dict:
        target_hdf_tree = {
            k: v for k, v in self.target_props.items() if k.startswith("/")
        }
        if self.source_props["type"] == "hdf5":
            assert isinstance(self.source_tree, HDF5Dict)
            if not target_hdf_tree:
                return self.source_tree

            target_tree = copy.deepcopy(self.source_tree)
            # Build new tree before setting attributes
            for path, items in target_hdf_tree.items():
                if "h5path" not in items:
                    continue

                target_tree[path] = self.source_tree[items["h5path"]]
                if items["h5path"] != path and items["h5path"] in target_tree:
                    target_tree.pop(items["h5path"])

        elif self.source_props["type"] == "csv":
            assert isinstance(self.source_tree, dict)
            target_tree = HDF5Dict({})

            for path, items in target_hdf_tree.items():
                if "col" not in items:
                    continue

                target_tree[path] = {
                    "_kind": "linear",  # _col
                    "_name": items["col"],
                    "_data": self.source_tree[items["col"]],
                    "_dtype": HDF5Dict._from_np()[self.source_tree[items["col"]].dtype],
                }

        for path, items in target_hdf_tree.items():
            if "attrs" not in items:
                continue

            for var, attr in items["attrs"].items():
                tokens = attr.split(".")
                if len(tokens) != 2:
                    raise ValueError(f"Invalid attribute: {attr}")

                prop_path = tokens[0]
                prop = tokens[1]

                self.set_attr(target_tree, path, prop_path, var, prop)

        return HDF5Dict(target_tree)

    def set_attr(self, target_tree: dict, path: str, prop_path: str, var: str, prop: str):
        target_tree[path] = {
            **target_tree.get(path, {}),
            "_attrs": {
                **target_tree.get(path, {}).get("_attrs", {}),
                var: self.get_attr(target_tree, prop_path, prop),
            },
        }

    def get_attr(self, target_tree: dict, prop_path: str, prop: str):
        if not target_tree[prop_path].get("_data"):
            raise ValueError(f"Path doesn't contain any data: {prop_path}")

        return self.attr_dict[prop](target_tree[prop_path]["_data"])

    @cached_property
    def attr_dict(self) -> dict:
        return {
            "max": lambda data: data.max(),
            "min": lambda data: data.min(),
            "mean": lambda data: data.mean(),
            "median": lambda data: data.median(),
            "length": lambda data: data.size,
        }

    def __parse_to_csv(self) -> pd.DataFrame | None:
        if self.source_props["type"] == "csv":
            return pd.DataFrame(self.source_tree)

    def __set_source_props(self) -> None:
        props: dict[str, Any] = {
            "path": self.network_dir / self.network_name.with_suffix(".hdf5")
            if self.source_config["path"] == "default"
            else Path(self.source_config["path"])
        }
        if props["path"].suffix.lower() not in HDF_EXTENSIONS + CSV_EXTENSIONS:
            raise ValueError(f"Unsupported target format found: {props['path']}")

        props["type"] = (
            "csv" if props["path"].suffix.lower() in CSV_EXTENSIONS else "hdf5"
        )
        if props["type"] == "csv":
            props["delimiter"] = self.target_config.get("delimiter", " ")
            props["comment"] = self.target_config.get("comment", "#")

        self.target_props = props

    def __set_target_props(self) -> None:
        props: dict[str, Any] = {
            "path": Path(self.target_config.get("path", self.source_props["path"].name))
        }
        if props["path"].suffix.lower() not in HDF_EXTENSIONS + CSV_EXTENSIONS:
            raise ValueError(f"Unsupported target format found: {props['path']}")

        props["type"] = (
            "csv" if props["path"].suffix.lower() in CSV_EXTENSIONS else "hdf5"
        )
        if props["type"] == "hdf5":
            props["default_group"] = self.target_config.get("default_group", "/")
        elif props["type"] == "csv":
            props["delimiter"] = self.target_config.get("delimiter", " ")
            props["comment"] = self.target_config.get("comment", "#")

        self.target_props = props

    def __get_source_tree(self) -> dict[str, Any]:
        if self.source_props["type"] == "hdf5":
            return HDF5Dict(self.source_props["path"]).flatten()

        df = pd.read_csv(
            self.source_props["path"],
            sep=self.source_props["delimiter"],
            comment=self.source_props["comment"],
            usecols=self.source_config.get("cols", None),
        )
        return {col: df[col].to_numpy() for col in df.columns}
