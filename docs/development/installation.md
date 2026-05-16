---
tags:
    - Development
    - Installation
icon: lucide/monitor-down
---

# Installation

## Prerequisites

- Python 3.9 or higher
- Git
- (Optional) [uv](https://docs.astral.sh/uv/) - A fast Python package installer and resolver

Check your Python version:

```bash
python --version
```

## Development Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/tgrassi/jaff.git
cd jaff
```

### Step 2: Create a Virtual Environment

It's strongly recommended to use a virtual environment for development:

=== "Using venv"

    ```bash
    # Create virtual environment
    python -m venv .venv

    # Activate (Linux/macOS)
    source .venv/bin/activate

    # Activate (Windows)
    .venv\Scripts\activate
    ```

=== "Using uv (Recommended)"

    ```bash
    # Create virtual environment with uv (much faster)
    uv venv

    # Activate
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate     # Windows
    ```

=== "Using conda"

    ```bash
    # Create conda environment
    conda create -n .venv python=3.11

    # Activate
    conda activate .venv
    ```

### Step 3: Install in Development Mode

Install JAFF in editable mode with all development dependencies:

=== "Using pip"

    ```bash
    # Install in editable mode with development dependencies
    pip install -e ".[dev]"
    ```

=== "Using uv (Recommended)"

    ```bash
    # Install in editable mode with development dependencies
    uv pip install -e ".[dev]"
    ```

The `-e` flag installs the package in "editable" mode, meaning changes you make to the source code are immediately reflected without reinstalling.

## Dependencies

### Core Dependencies

These are automatically installed with JAFF:

- `numpy (≥2.0.0)`- Numerical computations
- `scipy (≥1.13.0)` - Scientific computing
- `sympy (≥1.14.0)` - Symbolic mathematics
- `rich (≥15.0.0)` - Progress bars
- `h5py (≥3.9.0) `- HDF5 file support

### Development Dependencies

When installing with `[dev]`, the following additional packages are installed:

#### Testing Tools

- `pytest (≥7.0)` - Testing framework
- `pytest-cov` - Code coverage reporting
- `ruff` - Fast Python linter and formatter
- `check-jsonschema` - JSON schema validation

#### Documentation Tools

- `mkdocs (≥1.5.3)` - Documentation generator
- `mkdocs-material (≥9.5.0)` - Material theme for MkDocs
- `mkdocstrings[python] (≥0.24.0)` - API documentation from docstrings
- `mkdocstrings-python (≥1.7.0)` - Python handler for mkdocstrings
- `mkdocs-git-revision-date-localized-plugin (≥1.2.0)` - Git revision dates in docs
- `mkdocs-git-authors-plugin (≥0.7.0)` - Git authors information
- `mkdocs-minify-plugin (≥0.7.0)` - Minification for HTML/CSS/JS
- `pymdown-extensions (≥10.5)` - Advanced Markdown extensions
- `markdown (≥3.5.0)` - Markdown parser
- `pillow (≥10.0.0)` - Image processing for docs
- `cairosvg (≥2.7.0)` - SVG processing for docs

## Verifying Your Development Setup

After installation, verify everything is working:

```bash
# Check JAFF version
python -c "import jaff; print(jaff.__version__)"

# Test the CLI
jaffgen --help

# Run the test suite
pytest

# Check code style
ruff check .
```

## Running Tests

JAFF uses pytest for testing. See the [Testing Guide](testing.md) for details.

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=jaff --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run Specific Tests

```bash
# Run tests in a specific file
pytest tests/test_network.py

# Run tests matching a pattern
pytest -k "test_reaction"

# Run with verbose output
pytest -v
```

### Using uv to Run Tests

```bash
# uv can run commands in the virtual environment
uv run pytest

# With coverage
uv run pytest --cov=jaff
```

## Building Documentation

JAFF uses MkDocs with the Material theme for documentation.

### Build Documentation Locally

```bash
# Serve documentation with live reload (recommended for development)
mkdocs serve
```

Then open your browser to `http://127.0.0.1:8000`. The documentation will automatically rebuild when you save changes.

### Build Static Documentation

```bash
# Build static site in site/ directory
mkdocs build
```

### Using uv to Build Documentation

```bash
# Serve with live reload
uv run mkdocs serve

# Build static site
uv run mkdocs build
```

### Documentation Commands

```bash
# Serve with live reload (auto-updates on changes)
mkdocs serve

# Build static site
mkdocs build

# Deploy to GitHub Pages (maintainers only)
mkdocs gh-deploy

# Validate documentation links
mkdocs build --strict
```

## Code Style and Linting

JAFF uses Ruff for linting and formatting.

### Check Code Style

```bash
# Check for linting issues
ruff check .

# Check formatting
ruff format --check .
```

### Auto-Fix Issues

```bash
# Auto-fix linting issues where possible
ruff check --fix .

# Auto-format code
ruff format .

# Organize imports
ruff check --select I --fix
```

### Using uv

```bash
# Check with uv
uv run ruff check .
uv run ruff format --check .

# Fix with uv
uv run ruff check --fix .
uv run ruff format .

# Organize imports with uv
ruff check --select I --fix
```

## Updating Dependencies

### Update Development Installation

```bash
# Pull latest changes
git pull

# Update dependencies
pip install -e ".[dev]" --upgrade
```

With uv:

```bash
# Pull latest changes
git pull

# Update dependencies (uv automatically resolves to latest compatible versions)
uv pip install -e ".[dev]" --upgrade
```

## Working with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver written in Rust. It's significantly faster than pip for installing packages.

### Install uv

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Common uv Commands

```bash
# Create virtual environment
uv venv

# Install package
uv pip install package_name

# Install from requirements
uv pip install -r requirements.txt

# Install in editable mode
uv pip install -e ".[dev]"

# Run command in virtual environment
uv run pytest
uv run mkdocs serve
uv run python script.py

# Compile requirements (for reproducibility)
uv pip compile pyproject.toml -o requirements.txt
```

## IDE Setup

### VS Code

Recommended extensions:

- Python
- Pylance
- Ruff
- Even Better TOML

Settings (`.vscode/settings.json`):

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true,
    "python.linting.enabled": true,
    "ruff.format.args": ["--config", "pyproject.toml"]
}
```

### PyCharm

1. Set Python interpreter to your virtual environment
2. Enable pytest as the test runner
3. Install the Ruff plugin (if available)

### Zed

Settings (`.zed/settings.json`):

```json
{
    "languages": {
        "Python": {
            "language_servers": ["pyright"],
            "format_on_save": true
        }
    },

    "python": {
        "interpreter": ".venv/bin/python"
    },

    "formatter": {
        "external": {
            "command": "ruff",
            "arguments": ["format", "--config", "pyproject.toml", "-"]
        }
    },

    "lint": {
        "external": {
            "command": "ruff",
            "arguments": ["check", "--config", "pyproject.toml", "-"]
        }
    }
}
```

## Contributing

Before submitting a pull request:

1. **Run tests**: `pytest`
2. **Lint code**: `ruff check .`
3. **Format code**: `ruff format .`
4. **Build docs**: `mkdocs build --strict`
5. **Update documentation** if you've added features

See [Contributing Guide](contributing.md) for detailed contribution guidelines.
