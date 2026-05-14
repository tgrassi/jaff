---
tags:
    - Introduction
    - Installation
icon: lucide/monitor-down
---

# Installation

## Requirements

JAFF requires Python 3.9 or higher. Check your Python version:

```bash
python --version
```

## Installation Methods

### Method 1: Install from Source

For the latest development version:

```bash
# Clone the repository
git clone https://github.com/tgrassi/jaff.git
cd jaff

# Install the package
pip install -e .
```

Or using uv:

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

- **`jaffgen`** - Code generator for chemical reaction networks
    ```bash
    jaffgen --network networks/test.dat --template microphysics
    ```

You can also use the module invocation:

```bash
python -m jaff.generate --network networks/test.dat --template microphysics
```

## Testing Your Installation

Try loading a sample network and generating code:

```python
from jaff import Network

# Load a network file
net = Network("path/to/network.dat")
print(f"Loaded network with {len(net.species)} species")
print(f"and {len(net.reactions)} reactions")
```

Or from the command line:

```bash
# Generate C++ code from a template
jaffgen --network networks/test.dat --files template.cpp --outdir output/
```

## Troubleshooting

### ImportError: No module named 'jaff'

Make sure you've activated your virtual environment and that the installation completed successfully.

### Version Conflicts

If you encounter dependency conflicts:

```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing again
pip install jaff
```

With uv:

```bash
# uv handles upgrades automatically
uv pip install jaff
```

### NumPy/SciPy Installation Issues

On some systems, you may need to install NumPy and SciPy separately:

```bash
# Install scientific stack first
pip install numpy scipy

# Then install JAFF
pip install jaff
```

With uv (handles dependencies better):

```bash
uv pip install jaff
```

### Permission Errors

If you get permission errors on Linux/macOS:

```bash
# Install for current user only
pip install --user jaff

# Or use a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install jaff
```

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

To remove JAFF from your system:

=== "pip"

    ```bash
    pip uninstall jaff
    ```

=== "uv"

    ```bash
    uv pip uninstall jaff
    ```
