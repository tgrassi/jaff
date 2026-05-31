---
tags:
    - Api
---

# HDF5

`jaff.drivers.hdf5.HDF5`

The `HDF5` class reads and writes HDF5 files using the `HDF5Dict` data structure. It supports optional compression and converts between HDF5 groups/datasets and Python dictionaries.

## The `HDF5Dict` structure

`HDF5Dict` is a nested Python dictionary that mirrors the layout of an HDF5 file. The driver uses it as the bridge between disk and memory: `to_dict()` parses a file into one, and `from_dict()` walks one and writes it back out.

The mapping is direct:

- **Groups** (HDF5 folders) become **nested dictionaries**. Any key whose value is another dictionary creates a group.
- **Datasets** (HDF5 arrays) become **leaf dictionaries** — dictionaries containing the special `_`-prefixed keys described below.
- **Attributes** (metadata attached to a group, dataset, or the file root) go under a special `_attrs` key at that level.

### Leaf (dataset) keys

Each dataset is described by a dictionary with these keys:

| Key      | Required | Description                                                                                                                                                       |
| -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `_kind`  | yes      | `"linear"` for a plain N-D array, or `"compound"` for a structured/record array (multiple named columns).                                                         |
| `_data`  | yes      | The actual values — a NumPy array (or anything array-compatible).                                                                                                 |
| `_dtype` | yes      | The element type. For `"linear"`: a single JAFF dtype token string (e.g. `"f64"`). For `"compound"`: a `{field_name: dtype_token}` mapping, one entry per column. |
| `_attrs` | no       | `{attr_name: value}` written as HDF5 dataset attributes. Omit or leave empty if none.                                                                             |
| `_name`  | no       | Human-readable name for the dataset. Used as the CSV column/file name on export; falls back to the dictionary key if absent.                                      |

### Dtype tokens

`_dtype` values are short JAFF token strings rather than raw NumPy dtypes:

| Token                        | NumPy type                   |
| ---------------------------- | ---------------------------- |
| `i8`, `i16`, `i32`, `i64`    | signed ints                  |
| `u8`, `u16`, `u32`, `u64`    | unsigned ints                |
| `f16`, `f32`, `f64`, `f128`¹ | floats                       |
| `c64`, `c128`                | complex                      |
| `b`                          | bool                         |
| `s`                          | variable-length UTF-8 string |

¹ `f128` only on platforms where `numpy.float128` exists (typically Linux/macOS x86-64).

### Example

A file with a `reaction_coeff` group holding file-level attributes plus one `linear` and one `compound` dataset looks like this:

```python
hdf5_schema = {
    "reaction_coeff": {
        # Group-level HDF5 attributes.
        "_attrs": {
            "input_names": "temperature",
            "input_units": "K",
            "xlo": "Temp.low",
            "xhigh": "Temp.high",
            "spacing": "fast_log",
        },
        # A plain 1-D array dataset.
        "output_names": {
            "_kind": "linear",
            "_name": "output_names",   # optional; used as CSV column name
            "_data": data,
            "_dtype": "s",
            "_attrs": {},
        },
        # A structured (multi-column) dataset.
        "output_units": {
            "_kind": "compound",
            "_name": "output_units",   # optional; used as CSV file name
            "_data": data2,
            "_dtype": {                # one token per field
                "col1": "f32",
                "col2": "i32",
                "col3": "s",
            },
            "_attrs": {},
        },
    },
}
```

Here `reaction_coeff` is a group, its `_attrs` become attributes on that group, and `output_names`/`output_units` are the two datasets inside it. Pass this dict to `from_dict()` to write it, or get an equivalent structure back from `to_dict()`.

### Flatten / nested helpers

`HDF5Dict` can also be addressed by absolute path. `flatten()` collapses the nested tree into a flat `{ "/reaction_coeff/output_names": {leaf}, ... }` mapping, and `nested()` is the inverse. This is useful when you want to look up or assign a dataset by its full path rather than walking the nesting by hand.

Taking the `hdf5_schema` from above:

```python
from jaff.types import HDF5Dict

hd = HDF5Dict(hdf5_schema)

flat = hd.flatten()
# {
#     "/reaction_coeff": {"_attrs": {"input_names": "temperature", ...}},
#     "/reaction_coeff/output_names": {"_kind": "linear", "_data": ..., ...},
#     "/reaction_coeff/output_units": {"_kind": "compound", "_data": ..., ...},
# }

# Look up a single dataset by its full path.
leaf = flat["/reaction_coeff/output_names"]

# Rebuild the original nested structure.
hd.nested(flat) == hdf5_schema   # True
```

Each `_`-prefixed leaf is keyed by its absolute HDF5 path; group attributes land under the group's own path (`"/reaction_coeff"`), and file-level attributes under `"/"`.

## Constructor

`#!python HDF5(compression=None)`

**Parameters**

**compression** : _str or None, optional_
: HDF5 compression filter, e.g. `"gzip"`, `"lzf"`. Default `None`.

## Attributes

| Attribute     | Type          | Description        |
| ------------- | ------------- | ------------------ |
| `compression` | `str or None` | Compression filter |
