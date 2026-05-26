---
tags:
    - Api
icon: lucide/database
---

# jaff.drivers

I/O drivers for reading and writing network data in various formats.

## Classes and Functions

| Name | Description |
|------|-------------|
| [`HDF5`](hdf5.md) | Read/write HDF5 files with compression support |
| [`Db`](sqlite.md) | Low-level SQLite connection and query wrapper |
| [`JaffDb`](sqlite.md#jaffdb) | High-level JAFF-specific SQLite interface |
| [`Toml`](toml.md) | Read TOML configuration files |
| [`csv_to_df`](csv.md) | Load a CSV file into a pandas DataFrame |
| [`csv_to_hdf5`](csv.md#csv_to_hdf5) | Convert a CSV file to an HDF5 dataset |

## Quick Start

```python
from jaff.drivers import HDF5, Toml, JaffDb
from jaff.drivers.csv import csv_to_df, csv_to_hdf5

# HDF5
h5 = HDF5(compression="gzip")
data = h5.to_dict("output.hdf5")

# TOML
cfg = Toml("config.toml")
val = cfg.get_key("section")

# SQLite
db = JaffDb("network.db")
```
