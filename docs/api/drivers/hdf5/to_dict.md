---
tags:
    - Api
---

# HDF5.to_dict

`#!python to_dict(h5file)`

Reads an HDF5 file and returns its contents as a nested `HDF5Dict`.

**Parameters**

**h5file** : _h5py.File, Path, or str_
: HDF5 file to read.

**Returns**

_HDF5Dict_
: Nested dict mirroring the HDF5 hierarchy. Datasets become numpy arrays; attributes are stored under `"_attrs"`.
