---
tags:
    - User-guide
    - Code-generation
---

# Configuration File (`jaff.toml`)

A `jaff.toml` declares a [`jaffgen`](jaffgen.md) run once, so you don't repeat
CLI flags every time. It is loaded when you pass `--config <file>`, **or**
automatically when a file named `jaff.toml` turns up among the gathered template
files — which is how a bundled template (like `microphysics`) can ship its own
settings.

---

## Priority order

Every setting is resolved highest-wins, so the config file fills gaps the CLI
leaves and overrides constructor defaults:

1. Explicit CLI argument (e.g. `--network`)
2. `jaff.toml` value
3. `Network` constructor default

<!-- prettier-ignore -->
!!! note "Relative paths are resolved from the config file's directory"
    Any path that comes from the `jaff.toml` (network, funcfile, input/output
    dirs, table files) is resolved relative to **where the `jaff.toml` lives**,
    not the current working directory. Paths passed on the CLI are resolved
    relative to the CWD.

The smallest useful config is a single section — the bundled `microphysics`
template, for instance, ships only a `[radiation]` block:

```toml
[radiation]
bands = [13.6, "inf"]
power_law_index = 0
energy_density = false
rsl = 2.99792458e10
```

---

## `[jaffgen]` section

Controls the pipeline itself — mirrors the `jaffgen` CLI flags.

```toml
[jaffgen]
output_dir   = "../generated"          # where generated files are written
input_dir    = "."                     # directory of template files
input_files  = ["extra.cpp"]           # individual files (combined with input_dir)
template     = "microphysics"          # built-in template collection name
network      = "networks/GOW/GOW.jet"  # network file or built-in network name
default_lang = "cxx"                   # fallback language for unknown extensions
```

| Key            | Type        | Description                                                         |
| -------------- | ----------- | ------------------------------------------------------------------- |
| `output_dir`   | `str`       | Output directory (created if absent)                                |
| `input_dir`    | `str`       | Directory of template files to process                              |
| `input_files`  | `list[str]` | Individual template files; combined with `input_dir` and `template` |
| `template`     | `str`       | Built-in collection under `jaff/templates/generator/`               |
| `network`      | `str`       | Network file path, or a built-in network name                       |
| `default_lang` | `str`       | Fallback language for unrecognised extensions                       |

---

## `[network]` section

Sets `Network` constructor options.

```toml
[network]
label      = "GOW-2017"
funcfile   = "networks/GOW/GOW.jfunc"
replace_nH = true
errors     = false
```

| Key          | Type   | Default     | Description                                        |
| ------------ | ------ | ----------- | -------------------------------------------------- |
| `label`      | `str`  | file stem   | Human-readable network name                        |
| `funcfile`   | `str`  | auto-detect | Path to a `.jfunc` auxiliary file                  |
| `replace_nH` | `bool` | `true`      | Expand `nh` / `nhe` shorthands in rate expressions |
| `errors`     | `bool` | `false`     | Treat conservation violations as fatal             |

---

## `[radiation]` section

Configures the photochemistry radiation field. Present this block to enable
photochemistry radiation ode and jacobian radiation generation terms; omit it
(or give an empty `bands`) to leave it off.

```toml
[radiation]
bands           = [13.6, "inf"]    # band edges in eV; "inf" for an open upper bound
power_law_index = 0                # spectral power-law index
energy_density  = false            # true = energy density; false = photon density
rsl             = 2.99792458e10    # speed of light (cm/s). Used to configure reduced speed of light for solvers
```

| Key               | Type           | Default                 | Description                                                           |
| ----------------- | -------------- | ----------------------- | --------------------------------------------------------------------- |
| `bands`           | `list`         | `[]`                    | Band boundaries in eV; omit to disable photochemistry                 |
| `power_law_index` | `int or float` | `0`                     | Spectral index for band integration                                   |
| `energy_density`  | `bool`         | `false`                 | Radiation density variable type. `radeden` when `true` else `photden` |
| `rsl`             | `float`        | `constants.c.cgs.value` | Speed of light override (maps to the `c` constructor arg)             |

`power_law_index` is used to configure the weight factor of the photo-reaction cross-sections (Refer to the [Photochemistry](../designing-networks/photochemistry.md) section for more information).

## `[[table]]` section

A `[[table]]` array entry converts a data table from one format to another as
part of the generation run — typically to ship the lookup table that the
generated [interpolation functions](table-interpolation.md) read at runtime. One
block describes one conversion, with a `[table.source]` and a `[table.target]`.
Supported directions: **HDF5 → HDF5**, **CSV → HDF5**, and **CSV → CSV**.

### How the conversion works

The engine loads the source into a flat tree, builds a target tree from your
`[table.target]` headings, then writes it out:

1. **Source tree.** The source is flattened to a lookup keyed by absolute path.
   An HDF5 source becomes `{ "/co/TCO": <dataset>, "/co/L0CO": <dataset>, … }`; a
   CSV source becomes `{ "T0": <column>, "NeffCO": <column>, … }`.
   `path = "default"` is shorthand for the network's own rate table,
   `<network_dir>/<network_stem>.hdf5`.

2. **Target headings are output paths.** Every `[table.target]` key beginning
   with `/` is a path in the **output** HDF5 file. What you place under that
   heading says where its data comes from:
    - **`h5path = "/old/path"`** (HDF5 → HDF5) — move the source dataset/group at
      `/old/path` to this heading's path. The whole source tree is copied first,
      so datasets you don't remap pass through unchanged; a remapped source path
      is removed from its old location. Omit `h5path` to leave a dataset where it
      already is.
    - **`col = "ColName"`** (CSV → HDF5) — write the named CSV column as the
      dataset at this heading's path. Only columns named by a `col` are written;
      nested paths create the intermediate groups (e.g. `/co/1d/Temp`).

3. **Attributes.** A `.attrs` sub-table on a heading attaches HDF5 attributes to
   that path. Each attribute **value** is a `"/target/path.property"` reference —
   a statistic computed from the **target** tree at write time. Supported
   properties: `max`, `min`, `mean`, `median`, `length`. Because they read the
   target tree, the referenced path must exist in the output (e.g. the remapped
   path, not the original source path).

<!-- prettier-ignore -->
!!! warning "Attribute values are computed references, not literals"
    Every `.attrs` value must be of the form `"/path.property"` or a plain literal
    such as `units = "K"`.

`default_group` sets the output root group (default `/`). For CSV sides,
`delimiter` and `comment` configure parsing/writing.

### HDF5 → HDF5

Copy the source tree into a new file, remapping selected paths and attaching
computed attributes. Here `/co/TCO` is republished as `/temperature`:

```toml
[[table]]
[table.source]
path = "default"             # the network's own HDF5 rate table

[table.target]
path          = "GOW.hdf5"
default_group = "/"

[table.target."/temperature"]
h5path = "/co/TCO"           # move source /co/TCO here (other datasets copy through)

[table.target."/temperature".attrs]
tmax = "/temperature.max"    # computed from the data now at /temperature
npts = "/temperature.length"
```

### CSV → HDF5

Write named CSV columns as HDF5 datasets — the usual way to turn a
`co_1d.csv`-style table into the HDF5 file an interpolation routine reads:

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
col = "T0"                   # CSV column "T0" → dataset /co/1d/Temp

[table.target."/co/1d/Temp".attrs]
max       = "/co/1d/Temp.max"
min       = "/co/1d/Temp.min"
t0_length = "/co/1d/Temp.length"
```

### CSV → CSV

Select specific columns from one CSV and rewrite them, optionally changing the
delimiter:

```toml
[[table]]
[table.source]
delimiter = " "
comment   = "#"
path      = "networks/GOW/co_1d.csv"
cols      = ["T0", "NeffCO"]     # only these columns are kept

[table.target]
delimiter = ","
path      = "GOW.csv"
```

---

## Dummy example

The reference configuration below exercises every section.

```toml
[jaffgen]
output_dir   = "../generated"
input_dir    = "."
input_files  = ["../new.cpp", "test.cpp"]
template     = "microphysics"
network      = "networks/GOW/GOW.jet"
default_lang = "cxx"

[network]
label      = "GOW-generator"
funcfile   = "networks/GOW/GOW.jfunc"
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

[table.target."/temperature"]
h5path = "/co/TCO"

[table.target."/temperature".attrs]
tmax = "/temperature.max"
tmin = "/temperature.min"

# CSV → HDF5
[[table]]
[table.source]
delimiter = " "
comment   = "#"
path      = "networks/GOW/co_1d.csv"

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
path      = "networks/GOW/co_1d.csv"
cols      = ["T0", "NeffCO"]

[table.target]
delimiter = " "
comment   = "#"
path      = "GOW.csv"
```
