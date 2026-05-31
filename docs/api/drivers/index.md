---
tags:
    - Api
icon: phosphor/database
---

# jaff.drivers

The `jaff.drivers` subpackage provides I/O drivers for reading and writing data in the various file formats used by JAFF.

## Classes and Functions

| Name                                | Description                                    |
| ----------------------------------- | ---------------------------------------------- |
| [`HDF5`](hdf5/index.md)             | Read/write HDF5 files with compression support |
| [`Db`](sqlite/db/index.md)          | Low-level SQLite connection and query wrapper  |
| [`JaffDb`](sqlite/jaffdb/index.md)  | High-level JAFF-specific SQLite interface      |
| [`Toml`](toml/index.md)             | Read TOML configuration files                  |
| [`csv_to_df`](csv/csv_to_df.md)     | Load a CSV file into a pandas DataFrame        |
| [`csv_to_hdf5`](csv/csv_to_hdf5.md) | Convert a CSV file to an HDF5 dataset          |

## Quick Start

```python
from jaff.drivers import HDF5, Toml, JaffDb
from jaff.drivers.csv import csv_to_df, csv_to_hdf5

# HDF5
h5 = HDF5(compression="gzip")
data = h5.to_dict("input.hdf5")

# TOML
cfg = Toml("config.toml")
val = cfg.get_key("section")

# SQLite
db = Db("network.db")
```
