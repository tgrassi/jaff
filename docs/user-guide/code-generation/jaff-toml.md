---
tags:
    - User-guide
    - Code-generation
icon: lucide/settings-2
---

# Configuration File (`jaff.toml`)

A `jaff.toml` file lets you declare all `jaffgen` run settings once so you do not need to pass CLI flags every time. When `jaffgen` finds a `jaff.toml` inside the template directory it loads it automatically; you can also point to one explicitly with `--config`.

---

## Priority Order

Settings are resolved in this order (highest wins):

1. Explicit CLI argument (e.g. `--network`)
2. `jaff.toml` value
3. `Network` constructor default

---

## `[jaffgen]` Section

Controls the code-generation pipeline.

```toml
[jaffgen]
output_dir    = "../generated"          # where generated files are written
input_dir     = "."                     # directory of template files
input_files   = ["extra.cpp"]           # individual files (combined with input_dir)
template      = "microphysics"          # predefined template name
network       = "networks/GOW/GOW.dat"  # network file (required)
default_lang  = "cxx"                   # fallback language for unrecognised extensions
```

| Key            | Type           | Description |
| -------------- | -------------- | ----------- |
| `output_dir`   | `str`          | Output directory. Relative paths resolved from the config file's directory |
| `input_dir`    | `str`          | Directory of template files to process |
| `input_files`  | `list[str]`    | Individual template files; combined with `input_dir` |
| `template`     | `str`          | Name of a built-in template collection in `jaff/templates/generator/` |
| `network`      | `str`          | Path to the network file |
| `default_lang` | `str`          | Fallback language for files with unsupported extensions |

---

## `[network]` Section

Sets `Network` constructor options.

```toml
[network]
label       = "GOW-2017"
funcfile    = "networks/GOW/GOW.jfunc"
replace_nH  = true
errors      = false
```

| Key          | Type   | Default | Description |
| ------------ | ------ | ------- | ----------- |
| `label`      | `str`  | file stem | Human-readable network name |
| `funcfile`   | `str`  | auto-detect | Path to `.jfunc` auxiliary file |
| `replace_nH` | `bool` | `true`  | Expand `nh` / `nhe` shorthands in rate expressions |
| `errors`     | `bool` | `false` | Treat conservation violations as fatal errors |

---

## `[radiation]` Section

Configures the photochemistry radiation field.

```toml
[radiation]
bands             = [13.6, "inf"]    # band edges in eV; "inf" for open upper bound
power_law_index   = 0                # photon-number spectrum power-law index α
energy_density    = false            # true = energy density; false = photon density
rsl               = 2.99792458e10    # speed of light (cm/s)
```

| Key               | Type          | Default | Description |
| ----------------- | ------------- | ------- | ----------- |
| `bands`           | `list`        | `[]`    | Band boundaries in eV; omit to disable photochemistry |
| `power_law_index` | `int\|float`  | `0`     | Spectral index for band integration |
| `energy_density`  | `bool`        | `false` | Radiation density variable type |
| `rsl`             | `float`       | `c_cgs` | Speed of light override |

---

## `[[table]]` Section

Converts data tables between formats as part of the generation run. This section is an array of tables — each `[[table]]` block defines one source-to-target conversion.

### HDF5 → HDF5

Copy datasets and groups from one HDF5 file into a new one, optionally attaching attributes read from the source.

```toml
[[table]]
[table.source]
path = "default"         # "default" uses the network's own HDF5 rate table

[table.target]
path          = "GOW.hdf5"
default_group = "/"

[table.target."/metadata".attrs]
t_max = "/co/1d/Temp.max"   # value read from source path
t_min = "/co/1d/Temp.min"

[table.target."/co/1d"]
h5path = "/old_co/1d"       # source dataset/group path (defaults to same path)
attrs  = { temperature = "K" }

[table.target."/co/1d/Temp".attrs]
max          = "/co/1d/Temp.max"
min          = "/co/1d/Temp.min"
t0_length    = "/co/1d/Temp.length"
```

### CSV → HDF5

Read columns from a CSV and write them into an HDF5 file.

```toml
[[table]]
[table.source]
delimiter = " "
comment   = "#"
path      = "networks/GOW/co_1d.csv"

[table.target]
path          = "GOW.hdf5"
default_group = "/"

[table.target."/co/1d/Temp"]
col = "T0"                   # column name in the CSV

[table.target."/co/1d/Temp".attrs]
max      = "/co/1d/Temp.max"
min      = "/co/1d/Temp.min"
t0_length = "/co/1d/Temp.length"

[table.target."/co/1d"]
attrs = { temperature = "K" }
```

### CSV → CSV

Extract specific columns from one CSV and write them to another.

```toml
[[table]]
[table.source]
delimiter = " "
comment   = "#"
path      = "networks/GOW/co_1d.csv"
cols      = ["T0", "NeffCO"]     # only these columns are selected

[table.target]
delimiter = " "
comment   = "#"
path      = "GOW.csv"
```

### Target path syntax

Within a `[table.target]` section, keys that start with `/` are treated as HDF5 dataset or group paths. Append `.attrs` to attach metadata attributes.

Attribute values beginning with `/` are read from a corresponding path in the source file at runtime (late binding).

---

## Complete Example

The reference configuration below shows all sections in use.

```toml
[jaffgen]
output_dir   = "../../../generated"
input_dir    = "."
input_files  = ["../new.cpp", "test.cpp"]
template     = "microphysics"
network      = "../../../../../networks/GOW/GOW.dat"
default_lang = "cxx"

[network]
label      = "Gow-generator"
funcfile   = "../../../../../networks/GOW/GOW.jfunc"
replace_nH = true
errors     = false

[radiation]
bands           = [13.6, "inf"]
power_law_index = 0
energy_density  = false
rsl             = 2.99792458e10

# HDF5 → HDF5
[[table]]
[table.source]
path = "default"

[table.target]
path          = "GOW.hdf5"
default_group = "/"

[table.target."/metadata".attrs]
t_max = "/co/1d/Temp.max"
t_min = "/co/1d/Temp.min"

[table.target."/co/1d"]
h5path = "/old_co/1d"
attrs  = { temperature = "K" }

# CSV → HDF5
[[table]]
[table.source]
delimiter = " "
comment   = "#"
path      = "../../../../../networks/GOW/co_1d.csv"

[table.target]
path          = "GOW.hdf5"
default_group = "/"

[table.target."/co/1d/Temp"]
col = "T0"

# CSV → CSV
[[table]]
[table.source]
delimiter = " "
comment   = "#"
path      = "../../../../../networks/GOW/co_1d.csv"
cols      = ["T0", "NeffCO"]

[table.target]
delimiter = " "
comment   = "#"
path      = "GOW.csv"
```
