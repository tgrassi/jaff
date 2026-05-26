---
tags:
    - Api
    - Code-generation
---

# Codegen

`jaff.codegen.codegen.Codegen`

Multi-language code generator for chemical reaction networks. Generates rate coefficients, flux calculations, ODE right-hand sides, and analytical Jacobians using SymPy with optional common subexpression elimination (CSE).

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
| `net` | `Network` | The reaction network |
| `lang` | `str` | Normalized language id (e.g. `"cxx"`) |
| `lb`, `rb` | `str` | Left/right brackets for 1D arrays |
| `mlb`, `mrb` | `str` | Left/right brackets for 2D arrays |
| `matrix_sep` | `str` | Separator for 2D indices (e.g. `"]["` or `", "`) |
| `assignment_op` | `str` | Assignment operator |
| `line_end` | `str` | Statement terminator (`";"` or `""`) |
| `code_gen` | `Callable` | SymPy code generation function |
| `ioff` | `int` | Default index offset (0 or 1) |
| `comment` | `str` | Comment prefix (`"//"`, `"!!"`, `"#"`) |
| `types` | `dict` | Type declaration strings |
| `extras` | `dict` | Additional language-specific attributes |
