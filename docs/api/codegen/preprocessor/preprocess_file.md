---
tags:
    - Api
    - Code-generation
---

# preprocess_file

`#!python preprocess_file(fname, dictionary, comment="!!", add_header=True, path_build=None)`

Preprocesses a single template file, substituting pragma blocks and writing to `path_build`. Comment style is auto-detected from extension when `comment="auto"`:

| Extension            | Comment prefix |
| -------------------- | -------------- |
| `.cpp`, `.hpp`, `.h` | `"//"`         |
| `.f90`, `.f`         | `"!!"`         |
| `.py`                | `"#"`          |
| `.cmake`             | `"#"`          |

**Parameters**

**fname** : _str or Path_
: Path to the template file.

**dictionary** : _dict\[str, str\]_
: Mapping from pragma keys (without `PREPROCESS_` prefix) to replacement strings.

**comment** : _str, optional_
: Comment prefix. Use `"auto"` for extension-based detection. Default `"!!"`.

**add_header** : _bool, optional_
: Prepend auto-generated header. Default `True`.

**path_build** : _str, Path, or None, optional_
: Output directory. Defaults to current working directory.
