---
tags:
    - Api
---

# csv_to_hdf5

`#!python csv_to_hdf5(file, outfile, group_path="", hdf5_key="", flatten_columns=[], as_table=False, *args, **kwargs)`

Reads a CSV file and writes it into an HDF5 file. Appends to the HDF5 file if it already exists.

Supports three storage modes depending on the which parameters are passed:

- **Default** — each CSV column is stored as a separate 1-D dataset inside an HDF5 group at `<group_path>/<hdf5_key>`.
- **Table** (`as_table=True`) — the whole DataFrame is stored as a queryable PyTables-compatible table. Use this column metadata is needed or you want to query the HDF5 file with pandas later.
- **Flatten** (`flatten_columns=[...]`) — like default, but the listed columns are deduplicated before storage (only unique, sorted values are kept). Useful for coordinate axes that repeat across rows, e.g. a column of X positions that appears once per data row but should be stored as a compact axis.

**Parameters**

**file** : _str or Path_
: Path to the source CSV file.

**outfile** : _str or Path_
: Path to the output HDF5 file. Extension replaced with `.hdf5` if not already a recognised HDF5 extension.

**group_path** : _str, optional_
: Parent HDF5 group under which the dataset or table is created. Default `""` (root).

**hdf5_key** : _str, optional_
: Name of the dataset or table inside the group. Defaults to the CSV filename stem.

**flatten_columns** : _list\[str\], optional_
: Column names to deduplicate before storage. These columns are reduced to their unique sorted values instead of storing every row. Cannot be combined with `as_table`. Default `[]`.

**as_table** : _bool, optional_
: Write the DataFrame as a PyTables-compatible HDF5 table instead of raw datasets. Cannot be combined with `flatten_columns`. Default `False`.

**\*args, \*\*kwargs**
: Forwarded to `pandas.read_csv`.
