---
tags:
    - Api
    - Code-generation
---

# Codegen

`jaff.codegen.codegen.Codegen`

The `Codegen` class generates source code for chemical reaction networks in multiple target languages. It produces rate coefficients, flux expressions, ODE right-hand sides, and analytical Jacobians using SymPy, with optional common subexpression elimination (CSE).

Supported languages: C++ (`cxx`, `cpp`, `c++`), C (`c`), Fortran 90 (`f90`, `fortran`), Python (`py`, `python`), Rust (`rust`, `rs`), Julia (`julia`, `jl`), R (`r`).

## Constructor

`#!python Codegen(network, lang="c++", brac_format="", matrix_format="")`

**Parameters**

**network** : *Network*
:   The chemical reaction network.

**lang** : *str, optional*
:   Target language. Default `"c++"`.

**brac_format** : *str, optional*
:   Override 1D bracket style: `"[]"`, `"()"`, `"{}"`, `"<>"`. Default `""` (language default).

**matrix_format** : *str, optional*
:   Override 2D format: `"[]"`, `"[,]"`, `"()"`, `"(,)"`, `"{}"`, `"{,}"`, `"<>"`, `"<,>"`. Default `""`.

**Raises**

*ValueError*
:   If `lang`, `brac_format`, or `matrix_format` is not recognized.

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `net` | `Network` | The reaction network being code-generated |
| `lang` | `str` | Canonical language identifier (e.g. `"cxx"`, `"fortran"`, `"python"`) |
| `lb`, `rb` | `str` | Left and right bracket characters for 1-D array indexing (e.g. `"["` and `"]"`) |
| `mlb`, `mrb` | `str` | Left and right bracket characters for 2-D array indexing |
| `matrix_sep` | `str` | Index separator for 2-D arrays (e.g. `"]["` for C-style, `", "` for Fortran) |
| `assignment_op` | `str` | Assignment operator for the target language (`"="` for most, `"<-"` for R) |
| `line_end` | `str` | Statement terminator for the target language (`";"` for C/C++/Rust, `""` for others) |
| `code_gen` | `Callable` | SymPy printer function used to serialise symbolic expressions |
| `ioff` | `int` | Default array index offset (`0` for C/C++/Python/Rust, `1` for Fortran/Julia/R) |
| `comment` | `str` | Single-line comment prefix for the target language (`"//"`, `"!!"`, or `"#"`) |
| `types` | `dict` | Mapping from generic type names to language-specific spellings (e.g. `{"double": "double "}` for C++) |
| `extras` | `dict` | Additional language-specific tokens such as type qualifiers and class specifiers |
