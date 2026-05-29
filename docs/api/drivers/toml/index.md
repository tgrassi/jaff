---
tags:
    - Api
---

# Toml

`jaff.drivers.toml.Toml`

The `Toml` class reads a TOML configuration file on construction and exposes its contents as a Python dictionary for key-based access. It implements the context manager protocol.

## Constructor

`#!python Toml(file)`

**Parameters**

**file** : *str or Path*
:   Path to the TOML file. Parsed immediately on construction.

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `file` | `Path` | Resolved path to the TOML file |
| `data` | `dict` | Complete parsed contents of the file as a Python dictionary |

## Example

Given a TOML file:

```toml
# config.toml
temperature = 300.0
species = ["H", "O", "H2O"]

[network]
host = "localhost"
port = 8080
```

Reading values with `get_key()`:

```python
from jaff.drivers.toml import Toml

t = Toml("config.toml")
temp = t.get_key("temperature")   # 300.0
network = t.get_key("network")    # {"host": "localhost", "port": 8080}
missing = t.get_key("flux")       # None

# Context manager form
with Toml("config.toml") as t:
    species = t.get_key("species")  # ["H", "O", "H2O"]
```
