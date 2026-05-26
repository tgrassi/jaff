---
tags:
    - Introduction
    - Installation
icon: lucide/monitor-down
---

# Installation

## Requirements

JAFF requires `python>=3.9`. Check your Python version:

```bash
python --version
```

## Installation Methods

<!-- prettier-ignore -->
!!! tip "Managing virtual environments"
    Although JAFF can be installed in a variety of ways, it is encouraged to use [uv](https://docs.astral.sh/uv/) to install jaff and manage it's virtual environment

### Install from Source

For the latest development version:

=== "pip"

    ```bash
    # Clone the repository
    git clone git@github.com:jaff-chemistry/jaff.git
    cd jaff

    # Install the package
    pip install -e .
    ```

=== "uv"

    ```bash
    # Clone the repository
    git clone https://github.com/tgrassi/jaff.git
    cd jaff

    # Install the package
    uv pip install -e .
    ```

## Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with other packages:

=== "venv"

    ```bash
    # Create virtual environment
    python -m venv .venv

    # Activate (Linux/macOS)
    source .venv/bin/activate

    # Activate (Windows)
    .venv\Scripts\activate

    # Install JAFF
    pip install jaff -e .
    ```

=== "conda"

    ```bash
    # Create conda environment
    conda create -n .venv python=3.11

    # Activate
    conda activate venv

    # Install JAFF
    pip install jaff -e .
    ```

=== "uv"

    ```bash
    # Create virtual environment with uv (faster)
    uv venv

    # Activate
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate     # Windows

    # Install JAFF
    uv pip install jaff -e .
    ```

## Verifying Installation

After installation, verify that JAFF is working correctly:

```bash
# Check JAFF version
python -c "import jaff; print(jaff.__version__)"

# Test the code generator CLI
jaffgen --help
```

You should see the JAFF code generator help message.

### Available Commands

After installation, JAFF provides the following command-line tools:

- **`jaffx`** - Quick command executor

```bash
jaffx export hdf5 --network networks/demos/demo1.jet --file demo.hdf5
```

- **`jaffgen`** - Code generator for chemical reaction networks

```bash
jaffgen --network networks/demos/demo1.jet --template microphysics
```

## Troubleshooting

### `ImportError`: No module named 'jaff'

Make sure you've activated your virtual environment and that the installation completed successfully.

### NumPy/SciPy Installation Issues

On some systems, if you are using pip, you may need to install `NumPy` and `SciPy` separately:

```bash
# Install scientific stack first
pip install numpy scipy
```

<!--### Permission Errors

If you get permission errors on Linux/macOS:

```bash
# Install for current user only
pip install --user jaff

# Or use a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install jaff
```-->

## Next Steps

Now that JAFF is installed:

- **Quick Start**: Follow the [Quick Start Guide](quickstart.md) to run your first network analysis
- **Basic Concepts**: Learn about [chemical networks and reactions](concepts.md)
- **User Guide**: Explore detailed [usage documentation](../user-guide/loading-networks.md)
- **Developer Guide**: If you want to contribute or develop JAFF, see the [Developer Installation Guide](../development/installation.md)

<!--
## Updating JAFF

To update to the latest version:

```bash
# Update from PyPI
pip install --upgrade jaff
```

Or with uv:

```bash
# Update from PyPI
uv pip install --upgrade jaff
```
-->

## Uninstalling

To remove JAFF from your system/venv:

=== "pip"

    ```bash
    pip uninstall jaff
    ```

=== "uv"

    ```bash
    uv pip uninstall jaff
    ```
