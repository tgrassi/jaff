---
tags:
    - Api
---

# Toml

`jaff.drivers.toml.Toml`

Reads a TOML configuration file and provides key-based access. Supports context manager protocol.

## Constructor

`#!python Toml(file)`

**Parameters**

**file** : *str or Path*
:   Path to the TOML file. Parsed immediately on construction.

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `file` | `Path` | Path to the TOML file |
| `data` | `dict` | Full parsed contents |
