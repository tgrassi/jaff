---
tags:
    - Api
    - Network
---

# to_jaff

`#!python to_jaff(filename)`

Serialize this network to a gzip-compressed `.jaff` JSON file for fast reloading. The output uses the `jaff.network_json` format marker and `schema_version = 1`. If the path does not already end with `.jaff` or `.jaff.gz`, the `.jaff` suffix is appended automatically.

**Parameters**

**filename** : _str or Path_
: Destination path. `.jaff` suffix appended if not already present.
