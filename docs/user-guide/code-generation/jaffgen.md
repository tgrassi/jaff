---
tags:
    - User-guide
    - Code-generation
---

# jaffgen

`jaffgen` is JAFF's command-line entry point for the **full code-generation
pipeline**. It gathers a set of [template files](template-syntax.md), loads a
chemical reaction network, runs the
[template engine](template-syntax.md) over each file, and writes the generated
source into an output directory.

```bash
jaffgen --network <file> [options]
```

---

## How it works

A `jaffgen` run is four phases:

1. **Resolve configuration** — merge three sources by priority (see
   [below](#configuration-priority)): explicit CLI flags, a
   [`jaff.toml`](jaff-toml.md) file, then `Network` constructor defaults.
2. **Gather template files** — from `--indir`, `--files`, and `--template`.
   These **combine** — a single run can pull from all three.
3. **Load the network** — exactly one `Network`, built from the resolved
   network/label/funcfile/radiation settings.
4. **Generate** — run [`TemplateParser`](template-syntax.md) on every gathered
   file and write the result to `--outdir`, keeping the original filename.

The mental model: _jaffgen is the template engine driven over a file set with
one loaded network behind it._

---

## Input sources

The three input flags are additive, not exclusive:

| Flag         | Adds                                                          |
| ------------ | ------------------------------------------------------------- |
| `--indir`    | Every file in a directory (non-recursive)                     |
| `--files`    | Specific individual files                                     |
| `--template` | A built-in collection from `jaff/templates/generator/<name>/` |

For `--template`, generator files are collected first; any **preprocessor** file
(`jaff/templates/preprocessor/<name>/`) whose name does not clash is appended —
so the generator always wins on a name collision.

---

## Arguments

### Network and network options

| Argument       | Description                                                                     |
| -------------- | ------------------------------------------------------------------------------- |
| `--network`    | Network file path **or** a built-in network name; required (CLI or `jaff.toml`) |
| `--label`      | Override the network label (defaults to the file stem)                          |
| `--funcfile`   | Path to a `.jfunc` auxiliary file; auto-detected when omitted; `"none"` to skip |
| `--replace-nH` | `--replace-nH` / `--no-replace-nH` — expand `nh`/`nhe` shorthands (default: on) |
| `--errors`     | `--errors` / `--no-errors` — exit on conservation violations instead of warning |

When `--network` is a bare name (a sub-directory of `networks/`), jaffgen picks
the first `.jet` file inside it.

### Output

| Argument   | Description                                                           |
| ---------- | --------------------------------------------------------------------- |
| `--outdir` | Output directory (created if absent; defaults to `<repo>/generated/`) |

### Input sources

| Argument     | Description                                             |
| ------------ | ------------------------------------------------------- |
| `--indir`    | Directory of template files                             |
| `--files`    | One or more individual template files (space-separated) |
| `--template` | Built-in template collection name                       |

### Code generation

| Argument | Description                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------- |
| `--lang` | Fallback language for files with unrecognised extensions. Choices: `c`, `cxx`, `fortran`, `python`, `rust`, `julia` |

### Configuration file

| Argument   | Description                                                                                            |
| ---------- | ------------------------------------------------------------------------------------------------------ |
| `--config` | Path to a [`jaff.toml`](jaff-toml.md); also auto-detected if a `jaff.toml` is among the gathered files |

---

## Configuration priority

Each setting is resolved highest-wins:

1. Explicit CLI flag (e.g. `--network`)
2. [`jaff.toml`](jaff-toml.md) value (from `--config`, or auto-detected)
3. `Network` constructor default

Paths taken from a `jaff.toml` are resolved **relative to the config file's
directory**; paths given on the CLI are resolved relative to the current
directory.

---

## Examples

### Generate from a template directory

```bash
jaffgen \
    --network networks/GOW/GOW.jet \
    --indir   templates/           \
    --outdir  output/
```

For predefined networks, the folder name can also be passed as the network

```bash
jaffgen \
    --network GOW                  \
    --indir   templates/           \
    --outdir  output/
```

### Process specific files with a language hint

`--lang` supplies a language for files whose extension JAFF doesn't map (here,
`.txt`):

```bash
jaffgen \
    --network networks/GOW/GOW.jet \
    --files   rates.txt odes.txt   \
    --lang    rust                 \
    --outdir  output/
```

### Use a built-in template collection

```bash
jaffgen \
    --network  networks/GOW/GOW.jet \
    --template microphysics         \
    --lang     cxx                  \
    --outdir   output/
```

<!-- prettier-ignore -->
!!! note "Templates that bundle build files need `--lang`"
    The `microphysics` collection ships non-source files (e.g. `Make.package`
    and an extension-less `_parameters`) alongside its `.cpp`/`.H` templates.
    `TemplateParser` infers the language from each file's extension and has no
    fallback for unknown ones, so pass `--lang cxx` to give it one. Without it
    the run aborts with *"files are not yet supported"*.

### Combine a template collection with custom files

```bash
jaffgen \
    --network  networks/GOW/GOW.jet \
    --template microphysics         \
    --files    custom_rhs.cpp       \
    --lang     cxx                  \
    --outdir   output/
```

### Drive everything from a config file

A `jaff.toml` can carry the network, inputs, output, and radiation settings, so
the command collapses to:

```bash
jaffgen --config jaff.toml
```

A bundled template can even supply its own config. The `microphysics` collection
ships a `jaff.toml` with a `[radiation]` block, so `--template microphysics`
auto-detects it and turns on photochemistry without any extra flags. See
[`jaff.toml`](jaff-toml.md) for the full schema.

---

## Built-in templates

Collections live under `src/jaff/templates/generator/`. List them with:

```bash
ls src/jaff/templates/generator/
```
