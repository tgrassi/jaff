---
tags:
    - Development
icon: lucide/git-pull-request
---

# Contributing to JAFF

Thank you for your interest in contributing to JAFF! This guide will help you get started.

## Table of Contents

<!--- [Code of Conduct](#code-of-conduct)-->

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Review Process](#review-process)

<!--## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and considerate in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others-->

## Getting Started

### Ways to Contribute

- **Report bugs** - Found a bug? Open an issue!
- **Suggest features** - Have an idea? We'd love to hear it
- **Fix issues** - Browse open issues and submit a PR
- **Improve docs** - Documentation can always be better
- **Add examples** - Share your use cases
- **Answer questions** - Help others in discussions

### Before You Start

1. Check if an issue already exists for your contribution
2. For major changes, open an issue first to discuss
3. Make sure you can run the tests locally
4. Read through this guide

## Development Setup

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/jaff.git
cd jaff
```

### Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n jaff python=3.11
conda activate jaff
```

### Install Development Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or if that doesn't work:
pip install -e .
pip install pytest black mypy ruff mkdocs-material
```

### Verify Installation

```bash
# Run tests
pytest

# Check code style
black --check src/
ruff check src/

# Type checking
mypy src/
```

## Making Changes

### Create a Branch

```bash
# Create a new branch for your changes
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions/modifications
- `refactor/` - Code refactoring

### Commit Messages

Write clear, descriptive commit messages:

```bash
# Good
git commit -m "Add support for GPU code generation"
git commit -m "Fix index offset bug in Fortran codegen"
git commit -m "docs: Update installation guide"

# Bad
git commit -m "Fixed stuff"
git commit -m "WIP"
git commit -m "update"
```

**Format:**

```
type: Short description (50 chars or less)

Longer description if needed. Explain what and why,
not how. Wrap at 72 characters.

Fixes #123
```

**Types:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `style:` - Formatting
- `chore:` - Maintenance

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_network.py

# Run with coverage
pytest --cov=jaff --cov-report=html

# Run specific test
pytest tests/test_network.py::test_load_network
```

### Writing Tests

Add tests for all new features and bug fixes:

```python
# tests/test_myfeature.py
import pytest
from jaff import Network

def test_my_new_feature():
    """Test description."""
    net = Network("networks/test.dat")
    result = net.my_new_feature()
    assert result == expected_value

def test_edge_case():
    """Test edge cases."""
    with pytest.raises(ValueError):
        # Code that should raise ValueError
        pass
```

### Test Coverage

- Aim for >80% code coverage
- Test both success and failure cases
- Include edge cases
- Add regression tests for bug fixes

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def my_function(arg1: int, arg2: str) -> bool:
    """Short description.

    Longer description if needed. Explain what the function
    does, not how it does it.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When something is wrong

    Example:
        >>> result = my_function(42, "test")
        >>> print(result)
        True
    """
    pass
```

### Type Hints

Add type hints to all new code:

```python
from typing import List, Dict, Optional

def process_species(
    species: List[str],
    options: Optional[Dict[str, int]] = None
) -> Dict[str, float]:
    """Process species list."""
    pass
```

### Documentation Files

Update relevant documentation in `docs/`:

```bash
# Build docs locally
cd docs
mkdocs serve

# View at http://localhost:8000
```

Add examples to documentation:

````markdown
## Example

```python
from jaff import Network

net = Network("network.dat")
# ...
```
````

````

## Submitting Changes

### Before Submitting

Checklist:

- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] Added docstrings
- [ ] Type hints added
- [ ] No merge conflicts

### Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name
````

Then on GitHub:

1. Click "New Pull Request"
2. Choose your branch
3. Fill out the PR template
4. Submit!

### Pull Request Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing

How to test these changes:

1. Step 1
2. Step 2

## Checklist

- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] Added type hints

## Related Issues

Fixes #123
```

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

```python
# Maximum line length: 88 characters (Black default)
# Use 4 spaces for indentation
# Use double quotes for strings

# Good
def compute_rates(network: Network, temperature: float) -> np.ndarray:
    """Compute reaction rates."""
    return network.get_rates(temperature)

# Avoid
def compute_rates(network,temperature):
    return network.get_rates(temperature)
```

### Formatting with Black

```bash
# Format all files
black src/ tests/

# Check without modifying
black --check src/

# Format specific file
black src/jaff/network.py
```

### Linting with Ruff

```bash
# Check for issues
ruff check src/

# Fix automatically where possible
ruff check --fix src/
```

### Type Checking with mypy

```bash
# Type check
mypy src/

# Strict mode
mypy --strict src/jaff/network.py
```

### Import Order

Use `isort` or follow this order:

```python
# Standard library
import os
import sys
from typing import List, Dict

# Third-party
import numpy as np
import sympy as sp

# Local
from jaff import Network
from jaff.codegen import Codegen
```

## Review Process

### What to Expect

1. **Automated Checks** - CI runs tests, linting, type checking
2. **Code Review** - Maintainers review your code
3. **Discussion** - Back-and-forth to improve the PR
4. **Approval** - Once approved, PR is merged

### Review Timeline

- Initial review: Usually within 1 week
- Follow-up: Within a few days
- Be patient - maintainers are volunteers!

### Responding to Reviews

```bash
# Make requested changes
git add .
git commit -m "Address review comments"
git push
```

Be respectful and open to feedback. Reviews make the code better!

## Development Tips

### Running Specific Tests

```bash
# Fast test subset
pytest tests/test_network.py -v

# Skip slow tests
pytest -m "not slow"

# Run with debugging
pytest --pdb
```

### Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()
```

### Building Documentation

```bash
# Serve locally
mkdocs serve

# Build static site
mkdocs build

# Deploy (maintainers only)
mkdocs gh-deploy
```

### Performance Profiling

```python
import cProfile

cProfile.run('my_function()')
```

## Getting Help

Need help? We're here to assist:

- **GitHub Discussions** - Ask questions
- **GitHub Issues** - Report problems
- **Pull Requests** - Get feedback on code

Don't be shy! We're happy to help new contributors.

## Recognition

Contributors are recognized in the following ways:

- Mentioned in release notes
- Listed in the GitHub contributions graph

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to JAFF!** 🎉

Your contributions help make JAFF better for everyone.

## See Also

- [Code Style Guide](code-style.md)
- [Testing Guide](testing.md)
