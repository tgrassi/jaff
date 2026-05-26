---
tags:
    - Api
---

# HDF5.from_dict

`#!python from_dict(h5file, h5dict)`

Writes a dictionary to an HDF5 file in append mode, creating groups and datasets as needed.

**Parameters**

**h5file** : _str or Path_
: Output HDF5 file path.

**h5dict** : _dict or HDF5Dict_
: Data to write. Nested dicts become HDF5 groups. Entries with a `"_kind"` key are written as datasets.
