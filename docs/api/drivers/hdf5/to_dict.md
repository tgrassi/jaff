---
tags:
    - Api
---

# HDF5.to_dict

`#!python to_dict(h5file)`

Reads an HDF5 file (or sub-group) and returns its contents as a nested `HDF5Dict`.

**Parameters**

**h5file** : _h5py.File, h5py.Group, Path, or str_
: HDF5 source to read. An open `h5py.File` or a path/`str` is parsed from the
root; an open `h5py.Group` is parsed from that group onward. A
`"file.h5::/internal/group"` string (the `::` delimiter) opens the file and
parses from the named internal group onward.

**Returns**

_HDF5Dict_
: Nested dict mirroring the HDF5 hierarchy. Datasets become numpy arrays; attributes are stored under `"_attrs"`.
