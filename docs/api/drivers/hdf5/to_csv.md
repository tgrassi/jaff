---
tags:
    - Api
---

# HDF5.to_csv

`#!python to_csv(h5file, outdir, sep=" ")`

Converts the datasets in an HDF5 file into CSV files inside `outdir`. The file is loaded into an [`HDF5Dict`](index.md#the-hdf5dict-structure) and its tree is walked group by group; how a dataset is written depends on its `_kind`:

- **`linear` datasets** — all `linear` datasets found at the *same* group level are treated as columns and concatenated side by side into a single CSV named after that group (`<group>.csv`; the root level falls back to `out.csv`). Each column header is the dataset's `_name` attribute, or its key if `_name` is absent.
- **`compound` datasets** — each one is written to its own CSV file, since a structured array already holds multiple named columns. The file is named after the dataset's `_name` attribute, or its key (`<name>.csv`).

Sub-groups are traversed recursively, so a nested HDF5 hierarchy produces one CSV per group of linear columns plus one CSV per compound dataset. `_attrs` metadata is not exported.

**Parameters**

**h5file** : _str or Path_
: Source HDF5 file.

**outdir** : _str or Path_
: Destination directory, created if it does not exist.

**sep** : _str, optional_
: Column separator. Default `" "`.

**Example**

Given an HDF5 file `rates.hdf5` with this structure:

```
/
└── rates/                  (group)
    ├── T            linear   _name="T"
    ├── k1           linear   _name="k1"
    ├── k2           linear   _name="k2"
    └── output_units compound _name="output_units"  (col1, col2, col3)
```

```python
from jaff.drivers import HDF5

HDF5().to_csv("rates.hdf5", "out/", sep=",")
```

produces two files in `out/`:

- `rates.csv` — the three `linear` datasets merged as columns:

  ```
  T,k1,k2
  100.0,1.2e-10,3.4e-11
  200.0,2.3e-10,4.5e-11
  ```

- `output_units.csv` — the `compound` dataset, one column per field:

  ```
  col1,col2,col3
  1.5,3,cm3/s
  2.5,4,s-1
  ```
