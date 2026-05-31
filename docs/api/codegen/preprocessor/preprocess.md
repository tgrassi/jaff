---
tags:
    - Api
    - Code-generation
---

# preprocess

`#!python preprocess(path, fnames, dictionaries, comment="!!", add_header=True, path_build=None)`

Preprocesses a list of template files and copies all remaining files in `path` to the build directory.

**Parameters**

**path** : _str or Path_
: Directory containing template files.

**fnames** : _str or list\[str\]_
: File name(s) to preprocess. Non-listed files are copied unchanged.

**dictionaries** : _dict\[str, str\] or list\[dict\[str, str\]\]_
: Pragma replacement dictionaries, one per file. A single dict applies to all files.

**comment** : _str, optional_
: Comment prefix marking pragmas. Default `"!!"`.

**add_header** : _bool, optional_
: Prepend auto-generated file header. Default `True`.

**path_build** : _str, Path, or None, optional_
: Output directory, created if needed. Defaults to current working directory.
