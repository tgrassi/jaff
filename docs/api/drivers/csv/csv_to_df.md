---
tags:
    - Api
---

# csv_to_df

`#!python csv_to_df(file, *args, **kwargs)`

Reads a CSV file into a pandas DataFrame.

**Parameters**

**file** : _Path_
: Path to the CSV file.

**\*args, **kwargs\*\*
: Forwarded to `pandas.read_csv`.

**Returns**

_pandas.DataFrame_
: The CSV data as a DataFrame, with columns inferred from the file header.

**Raises**

_FileNotFoundError_
: If `file` does not exist.
