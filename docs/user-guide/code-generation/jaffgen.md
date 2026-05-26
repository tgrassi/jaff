---
tags:
    - User-guide
    - Code-generation
icon: lucide/terminal
---

# jaffgen

`jaffgen` is JAFF's command-line entry point for the full code-generation pipeline. It reads one or more template files containing `$JAFF` directives, loads a chemical reaction network, and writes the generated source files to an output directory.

```bash
jaffgen --network <file> [options]
```

---

## Input Sources

Three input modes can be combined freely in a single invocation:

| Flag         | Description |
| ------------ | ----------- |
| `--indir`    | Process all files in a directory |
| `--files`    | Process specific individual files |
| `--template` | Use a built-in template collection from `jaff/templates/generator/` |

When `--template` is given, generator files take precedence over preprocessor files of the same name.

---

## Arguments

### Network and network options

| Argument       | Description |
| -------------- | ----------- |
| `--network`    | Path to the network file (required, unless in `jaff.toml`) |
| `--label`      | Override the network label (defaults to file stem) |
| `--funcfile`   | Path to `.jfunc` auxiliary file; auto-detected when omitted; pass `"none"` to skip |
| `--replace-nH` | Expand `nh`/`nhe` shorthands in rate expressions (default: on) |
| `--errors`     | Exit on conservation violations instead of warning |

### Output

| Argument   | Description |
| ---------- | ----------- |
| `--outdir` | Output directory for generated files (default: `<jaff_package>/generated/`) |

### Input sources

| Argument     | Description |
| ------------ | ----------- |
| `--indir`    | Directory of template files |
| `--files`    | One or more individual template files |
| `--template` | Built-in template name |

### Code generation

| Argument | Description |
| -------- | ----------- |
| `--lang` | Default language for files with unrecognised extensions (`c`, `cxx`, `fortran`, `python`, `rust`, `julia`) |

### Configuration file

| Argument   | Description |
| ---------- | ----------- |
| `--config` | Path to a `jaff.toml` config file; auto-detected inside `--indir` when omitted |

---

## Configuration Priority

Settings are resolved in this order (highest wins):

1. Explicit CLI flag (e.g. `--network`)
2. `jaff.toml` value (auto-detected or from `--config`)
3. `Network` constructor default

---

## Examples

### Generate from a template directory

```bash
jaffgen \
    --network  networks/GOW/GOW.jet  \
    --indir    templates/             \
    --outdir   output/
```

### Use a built-in template collection

```bash
jaffgen \
    --network  networks/GOW/GOW.jet  \
    --template microphysics           \
    --outdir   output/
```

### Process specific files with a language hint

```bash
jaffgen \
    --network  networks/GOW/GOW.jet  \
    --files    rates.txt odes.txt     \
    --lang     rust                   \
    --outdir   output/
```

### Combine template collection with custom files

```bash
jaffgen \
    --network  networks/GOW/GOW.jet  \
    --template microphysics           \
    --files    custom_rhs.cpp         \
    --outdir   output/
```

### Load settings from a config file

```bash
jaffgen --config jaff.toml
```

### Load network with a custom funcfile and label

```bash
jaffgen \
    --network  networks/GOW/GOW.jet      \
    --funcfile networks/GOW/GOW.jfunc    \
    --label    "GOW-2017"                \
    --outdir   output/
```

### Enable photochemistry with a config file

When radiation bands are required, set them in `jaff.toml`:

```toml
[jaffgen]
network  = "networks/h_photoionization/h_photo.jet"
outdir   = "output/"
template = "my_photo_template"

[radiation]
bands           = [13.6, "inf"]
power_law_index = 0
energy_density  = false
```

Then run:

```bash
jaffgen --config jaff.toml
```

---

## Built-in Templates

Built-in template collections live in `src/jaff/templates/generator/`. List them by inspecting that directory:

```bash
ls src/jaff/templates/generator/
```

---

## Python API

The same pipeline is available programmatically via `TemplateParser`:

```python
from jaff import Network
from jaff.codegen import TemplateParser
from pathlib import Path

net = Network("networks/GOW/GOW.jet")

for template_file in Path("templates/").iterdir():
    parser = TemplateParser(net, template_file)
    output = parser.parse_file()
    (Path("output/") / template_file.name).write_text(output)
```
