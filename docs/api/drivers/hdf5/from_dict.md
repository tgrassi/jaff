---
tags:
    - Api
---

# HDF5.from_dict

`#!python from_dict(h5file, h5dict)`

Writes an `HDF5Dict` (or a plain Python dict with the same structure) to an HDF5 file. The file is opened in append mode, so existing groups and datasets are preserved; only keys present in `h5dict` are written or overwritten. Plain `dict` objects are automatically wrapped in an `HDF5Dict` before writing.

See the [`HDF5Dict` structure](index.md#the-hdf5dict-structure) for the expected dictionary layout.

**Parameters**

**h5file** : _str or Path_
: Path to the output HDF5 file. Created if it does not exist; opened in append mode if it does.

**h5dict** : _dict or HDF5Dict_
: Data to write. Nested plain dicts become HDF5 groups. Any dict containing a `"_kind"` key is treated as a dataset leaf and written as an HDF5 dataset.
