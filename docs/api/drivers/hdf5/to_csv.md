---
tags:
    - Api
---

# HDF5.to_csv

`#!python to_csv(h5file, outdir, sep=" ")`

Converts all datasets in an HDF5 file to individual CSV files.

**Parameters**

**h5file** : _str or Path_
: Source HDF5 file.

**outdir** : _str or Path_
: Destination directory, created if it does not exist.

**sep** : _str, optional_
: Column separator. Default `" "`.
