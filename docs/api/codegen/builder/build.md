---
tags:
    - Api
    - Code-generation
---

# build

`#!python build(template="python_solve_ivp", output_dir=None)`

Invokes the named plugin template to generate a complete solver from the network. Copies all template files to the output directory and runs the plugin's preprocessing step.

**Parameters**

**template** : _str, optional_
: Plugin template name. Built-in options: `"python_solve_ivp"`, `"fortran_dlsodes"`, `"kokkos_ode"`, `"microphysics"`. Default `"python_solve_ivp"`.

**output_dir** : _str or None, optional_
: Output directory. Defaults to current working directory.

**Returns**

_str_
: Absolute path to the output directory.

**Raises**

_SystemExit_
: If the template plugin module is not found.
