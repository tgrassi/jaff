---
tags:
    - Api
    - Code-generation
---

# get_language_tokens

`#!python Codegen.get_language_tokens()`

Static method. Returns the full language token dictionary mapping canonical language names to their code-generation configuration. Result is cached.

**Returns**

_dict\[str, LangModifier\]_
: Mapping from canonical language name to a `LangModifier` `TypedDict`. Supported keys: `"cxx"`, `"c"`, `"fortran"`, `"python"`, `"rust"`, `"julia"`, `"r"`. (User-facing aliases like `"c++"`, `"cpp"`, `"py"`, `"f90"`, `"rs"`, `"jl"` are normalised to these canonical names before lookup.)

Each `LangModifier` is a `TypedDict` with the following fields:

| Key | Type | Description |
| --- | --- | --- |
| `brac` | `str` | Two-character left/right bracket pair for 1-D array indexing (e.g. `"[]"` for C/C++/Python/Rust/Julia/R, `"()"` for Fortran). |
| `assignment_op` | `str` | Assignment operator (`"="` for most languages, `"<-"` for R). |
| `line_end` | `str` | Statement terminator (`";"` for C/C++/Rust, `""` for Python/Fortran/Julia/R). |
| `matrix_sep` | `str` | Separator between row and column indices for 2-D access (`"]["` for C/C++/Python/Rust/Julia, `", "` for Fortran/R). |
| `code_gen` | `Callable[..., str]` | SymPy printer used to serialise expressions (`sympy.cxxcode`, `sympy.ccode`, `sympy.fcode`, `sympy.pycode`, `sympy.rust_code`, `sympy.julia_code`, `sympy.rcode`). |
| `idx_offset` | `int` | Base index added to all array subscripts (`0` for C/C++/Python/Rust, `1` for Fortran/Julia/R). |
| `comment` | `str` | Single-line comment prefix (`"//"` for C/C++/Rust, `"!"` for Fortran, `"#"` for Python/Julia/R). |
| `types` | `dict[str, str]` | Mapping from generic type name (`"int"`, `"float"`, `"double"`, `"bool"`) to language-specific spelling, e.g. `{"double": "double "}` for C/C++, `{"double": "f64 "}` for Rust, `{"double": "Float64 "}` for Julia. Empty `{}` for Python/Fortran/R. |
| `extras` | `dict[str, Any]` | Miscellaneous language-specific tokens. Common keys: `"type_qualifier"` (`"const "` for C/C++/Rust/Julia) and `"class_specifier"` (`"static "` for C/C++, `"save "` for Fortran, `""` for Rust/Julia). Empty `{}` for Python/R. |

**Example**

```python
tokens = Codegen.get_language_tokens()
tokens["cxx"]["brac"]           # "[]"
tokens["fortran"]["idx_offset"] # 1
tokens["r"]["assignment_op"]    # "<-"
```
