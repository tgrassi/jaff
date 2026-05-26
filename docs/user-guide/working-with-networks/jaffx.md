---
tags:
    - User-guide
    - Network
icon: lucide/terminal
---

# jaffx

`jaffx` is JAFF's command-line tool for quick network inspection and rate-coefficient export. It does **not** run the code-generation pipeline — use it when you want to inspect or tabulate rates without writing templates.

```bash
jaffx <command> <subcommand> --network <file> [options]
```

---

## Commands

`jaffx` exposes two top-level commands: `export` and `get`.

---

## `jaffx export`

Export rate coefficients in a tabulated format.

### `export hdf5`

Write rate coefficients as a function of temperature to an HDF5 file.

```bash
jaffx export hdf5 \
    --network networks/GOW/GOW.jet \
    --file    rates.h5             \
    --tmin    10                   \
    --tmax    1e4                  \
    --nT      200
```

**Arguments**

| Argument       | Description |
| -------------- | ----------- |
| `--network`    | Path to the network file (required) |
| `--file`, `-f` | Output file path (default: derived from network name) |
| `--tmin`       | Minimum temperature for tabulation (default: reaction minimum) |
| `--tmax`       | Maximum temperature for tabulation (default: reaction maximum) |
| `--nT`         | Number of temperature points (initial guess for adaptive sampling) |
| `--err-tol`    | Relative interpolation error tolerance; adaptive sampling is disabled when unset |
| `--rate-min`   | Adaptive refinement not applied to rates below this floor |
| `--rate-max`   | Rates above this ceiling are clipped to prevent overflow |
| `--fast-log`   | Sample equally in `#!python fast_log2(T)` space instead of `#!python log(T)` |
| `--include-all`| Include all reactions (non-tabulatable ones are set to NaN) |
| `--verbose`, `-v` | Print progress during adaptive refinement |
| `--label`      | Network label override |
| `--funcfile`   | Path to auxiliary function file |
| `--replace-nh` | Standardise H-density symbols |

### `export txt`

Write rate coefficients to a plain whitespace-separated text file. Accepts the same arguments as `export hdf5`.

```bash
jaffx export txt \
    --network networks/GOW/GOW.jet \
    --file    rates.txt            \
    --tmin    10 --tmax 1e4 --nT 100
```

### `export jaff`

Serialise the entire parsed network to a gzip-compressed JSON `.jaff` file. This binary format can be re-loaded by `Network` directly and skips re-parsing the original network file.

```bash
jaffx export jaff \
    --network networks/GOW/GOW.jet \
    --file    GOW.jaff
```

---

## `jaffx get`

Query scalar network properties.

### `get num-species`

Print the total species count.

```bash
jaffx get num-species --network networks/GOW/GOW.jet
```

```text
Total number of species: 12
```

### `get num-reactions`

Print the total reaction count.

```bash
jaffx get num-reactions --network networks/GOW/GOW.jet
```

```text
Total number of reactions: 51
```

---

## Shared Network Arguments

Every sub-command accepts these common options:

| Argument       | Description |
| -------------- | ----------- |
| `--network`    | Path to the network file |
| `--label`      | Override the network label |
| `--funcfile`   | Path to `.jfunc` auxiliary file (auto-detected when omitted) |
| `--replace-nh` | `--replace-nh` / `--no-replace-nh` — expand H-density shorthands |

---

## Examples

```bash
# Quick species count
jaffx get num-species --network networks/h_photoionization/h_photo.jet

# Export 500-point temperature table to HDF5 with adaptive sampling
jaffx export hdf5 \
    --network networks/GOW/GOW.jet \
    --file    GOW_rates.h5         \
    --tmin 10 --tmax 1e5 --nT 500  \
    --err-tol 1e-4

# Export plain-text table including all reactions (NaN for non-tabulatable)
jaffx export txt \
    --network  networks/GOW/GOW.jet \
    --file     GOW_rates.txt        \
    --include-all

# Serialise network for fast re-loading
jaffx export jaff \
    --network networks/GOW/GOW.jet \
    --file    GOW.jaff
```
