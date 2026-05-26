---
tags:
    - Api
---

# HDF5

`jaff.drivers.hdf5.HDF5`

Reads and writes HDF5 files using a dict-like interface. Supports optional compression and converts between HDF5 groups/datasets and Python dictionaries.

## Constructor

`#!python HDF5(compression=None)`

**Parameters**

**compression** : *str or None, optional*
:   HDF5 compression filter, e.g. `"gzip"`, `"lzf"`. Default `None`.

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `compression` | `str or None` | Compression filter |
