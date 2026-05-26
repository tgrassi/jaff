---
tags:
    - Api
---

# csv_to_hdf5

`#!python csv_to_hdf5(file, outfile, group_path="", hdf5_key="", flatten_columns=[], as_table=False, *args, **kwargs)`

Reads a CSV file and writes it to an HDF5 file as a dataset or table.

**Parameters**

**file** : _str or Path_
: Input CSV file.

**outfile** : _str or Path_
: Output HDF5 file. Extension forced to `.hdf5`.

**group_path** : _str, optional_
: HDF5 group path. Default `""` (root).

**hdf5_key** : _str, optional_
: Dataset key name. Defaults to the CSV file stem.

**flatten_columns** : _list[str], optional_
: Columns to flatten into dataset. Cannot use with `as_table`. Default `[]`.

**as_table** : _bool, optional_
: Write as PyTables table. Cannot use with `flatten_columns`. Default `False`.

**\*args, **kwargs\*\*
: Forwarded to `pandas.read_csv`.

**Raises**

_FileNotFoundError_
: If `file` does not exist.

_ValueError_
: If both `as_table` and `flatten_columns` are specified.
