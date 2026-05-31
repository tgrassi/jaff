---
tags:
    - Api
---

# get_key

`#!python get_key(key)`

Returns the value of a top-level key from the parsed TOML file. For nested sections, the value is a dict; for scalar keys, it is a string, int, float, or bool depending on the TOML type. Returns `None` instead of raising an error if the key does not exist.

**Parameters**

**key** : _str_
: Top-level TOML key to look up.

**Returns**

_any_
: The value associated with `key`, or `None` if the key is not present in the file.
