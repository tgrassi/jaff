---
tags:
    - Development
icon: lucide/chart-no-axes-gantt
---

# Code Style

## Python Version

JAFF supports Python 3.9 and higher. Write code that is compatible with Python 3.9+.

```python
# Good - use typing module for compatibility
from typing import List, Dict, Optional

def process(items: List[str]) -> Dict[str, int]:
    pass

# Avoid - built-in generic syntax requires Python 3.10+
def process(items: list[str]) -> dict[str, int]:
    pass
```

## Code Formatting

Use Ruff for both formatting and linting, replacing Black entirely.

```bash
# Format all code
ruff format src/ tests/

# Check formatting without modifying (Black --check equivalent)
ruff format --check src/

# Format specific file
ruff format src/jaff/network.py
```

## Naming Conventions

### Variables and Functions

Use `snake_case`:

```python
# Good
user_name = "Alice"
def calculate_rate(temperature):
    pass

# Avoid
userName = "Alice"
def CalculateRate(temperature):
    pass
```

### Classes

Use `PascalCase`:

```python
# Good
class Network:
    pass

class CodeGenerator:
    pass

# Avoid
class network:
    pass
```

### Constants

Use `UPPER_SNAKE_CASE`:

```python
# Good
MAX_ITERATIONS = 1000
DEFAULT_TEMPERATURE = 300.0

# Avoid
maxIterations = 1000
```

### Private Members

Prefix with underscore:

```python
class Network:
    def __init__(self):
        self._internal_data = []  # Private
        self.public_data = []     # Public

    def _helper_method(self):  # Private
        pass

    def public_method(self):   # Public
        pass
```

## Type Hints

### Always Use Type Hints

```python
# Good
def compute_rate(temperature: float, alpha: float) -> float:
    return alpha * temperature

# Avoid
def compute_rate(temperature, alpha):
    return alpha * temperature
```

### Import Types

```python
from typing import List, Dict, Optional, Union, Tuple, Any
from pathlib import Path
import numpy as np

def process_species(
    names: List[str],
    masses: np.ndarray,
    options: Optional[Dict[str, Any]] = None
) -> Tuple[List[str], np.ndarray]:
    pass
```

### Complex Types

```python
from typing import List, Dict, Union, Optional

# Type aliases for clarity
SpeciesDict = Dict[str, int]
RateExpression = Union[str, float]

def load_network(
    filename: str,
    species_map: Optional[SpeciesDict] = None
) -> Network:
    pass
```

## Docstrings

### Google Style

Use Google-style docstrings:

```python
def compute_rates(network: Network, temperature: float) -> np.ndarray:
    """Compute reaction rate coefficients.

    This function calculates rate coefficients for all reactions
    in the network at the specified temperature.

    Args:
        network: Chemical reaction network
        temperature: Gas temperature in Kelvin

    Returns:
        Array of rate coefficients in cm³/s

    Raises:
        ValueError: If temperature is negative

    Example:
        >>> net = Network("network.dat")
        >>> rates = compute_rates(net, 100.0)
        >>> print(rates[0])
        1.2e-10
    """
    if temperature < 0:
        raise ValueError("Temperature must be non-negative")
    return network.calculate_rates(temperature)
```

### Class Docstrings

```python
class Codegen:
    """Multi-language code generator for chemical networks.

    This class generates optimized code for evaluating reaction rates,
    ODEs, and Jacobians in multiple programming languages.

    Attributes:
        net: Chemical reaction network
        lang: Target programming language
        ioff: Array indexing offset (0 or 1)

    Example:
        >>> net = Network("network.dat")
        >>> cg = Codegen(network=net, lang="c++")
        >>> rates = cg.get_rates(use_cse=True)
    """

    def __init__(self, network: Network, lang: str = "c++"):
        """Initialize code generator.

        Args:
            network: Chemical reaction network
            lang: Target language (c++, c, fortran, python)
        """
        pass
```

### Module Docstrings

```python
"""Chemical reaction network module.

This module provides the Network class for loading and managing
chemical reaction networks from various file formats.

Example:
    >>> from jaff import Network
    >>> net = Network("network.dat")
"""
```

## Error Handling

### Specific Exceptions

```python
# Good
try:
    net = Network(filename)
except FileNotFoundError:
    print(f"File not found: {filename}")
except ValueError as e:
    print(f"Invalid network format: {e}")

# Avoid
try:
    net = Network(filename)
except:  # Too broad
    pass
```

### Custom Exceptions

```python
class NetworkError(Exception):
    """Base exception for network errors."""
    pass

class ParseError(NetworkError):
    """Error parsing network file."""
    pass

def load_network(filename: str) -> Network:
    try:
        return Network(filename)
    except ValueError as e:
        raise ParseError(f"Failed to parse {filename}: {e}")
```

### Error Messages

```python
# Good - descriptive
raise ValueError(f"Temperature must be positive, got {temp}")

# Avoid - vague
raise ValueError("Bad temperature")
```

<!--## Functions

### Single Responsibility

```python
# Good - single purpose
def calculate_rate(temperature: float, alpha: float, beta: float) -> float:
    return alpha * (temperature / 300) ** beta

def write_to_file(content: str, filename: str) -> None:
    with open(filename, 'w') as f:
        f.write(content)

# Avoid - multiple responsibilities
def calculate_and_save_rate(temperature, alpha, beta, filename):
    rate = alpha * (temperature / 300) ** beta
    with open(filename, 'w') as f:
        f.write(str(rate))
```

### Function Length

Keep functions short and focused (generally < 50 lines):

```python
# Good
def process_network(filename: str) -> Network:
    """Process network file."""
    net = load_network(filename)
    validate_network(net)
    return net

# If too long, split into smaller functions
```

### Arguments

```python
# Good - clear parameters
def compute_ode(
    species: List[str],
    reactions: List[Reaction],
    use_cse: bool = True
) -> str:
    pass

# Avoid - too many positional arguments
def compute_ode(species, reactions, cse, optimize, cache, debug):
    pass
```

## Classes

### Keep Classes Focused

```python
# Good - single responsibility
class Network:
    """Represents a chemical reaction network."""

    def load(self, filename: str) -> None:
        pass

    def validate(self) -> bool:
        pass

# Avoid - doing too much
class NetworkManager:
    """Does everything."""
    pass
```

### Properties vs Methods

```python
class Network:
    @property
    def num_species(self) -> int:
        """Number of species (property - no computation)."""
        return len(self._species)

    def calculate_rates(self, temperature: float) -> np.ndarray:
        """Calculate rates (method - requires computation)."""
        return self._compute_rates(temperature)
```
-->

## Testing Style

### Test Function Names

```python
# Good - descriptive
def test_network_loads_krome_format():
    pass

def test_codegen_raises_error_for_invalid_language():
    pass

# Avoid
def test1():
    pass
```

### Test Organization

```python
class TestNetwork:
    """Tests for Network class."""

    def test_load_from_file(self):
        """Test loading network from file."""
        pass

    def test_validate_species(self):
        """Test species validation."""
        pass
```

### Assertions

```python
# Good - clear assertions
assert len(net.species) == 35
assert net.label == "react_COthin"
assert_almost_equal(rate, 1.2e-10, decimal=15)

# Avoid - unclear
assert x
```

## Performance

### List Comprehensions

```python
# Good - fast
species_names = [s.name for s in network.species]

# Slower
species_names = []
for s in network.species:
    species_names.append(s.name)
```

### String Formatting

```python
# Good - f-strings (fast, readable)
message = f"Network has {n} species"

# Avoid - slow
message = "Network has " + str(n) + " species"
```

## Best Practices

### Use Context Managers

```python
# Good
with open(filename, 'w') as f:
    f.write(content)

# Avoid
f = open(filename, 'w')
f.write(content)
f.close()
```

### Use Pathlib

```python
from pathlib import Path

# Good
path = Path("networks") / "react.dat"
if path.exists():
    content = path.read_text()

# Avoid
import os
path = os.path.join("networks", "react.dat")
if os.path.exists(path):
    with open(path) as f:
        content = f.read()
```

### Early Returns

```python
# Good - early return
def process(value: Optional[int]) -> int:
    if value is None:
        return 0

    if value < 0:
        return -1

    return value * 2

# Avoid - nested if
def process(value):
    if value is not None:
        if value >= 0:
            return value * 2
        else:
            return -1
    else:
        return 0
```

## Code Review Checklist

Before submitting code:

- [x] Code formatted with ruff
- [x] Sort imports with ruff
- [x] No linting errors (ruff)
- [x] Type hints added
- [x] Docstrings written
- [x] Tests added/updated
- [x] No commented-out code
- [x] No hardcoded paths
- [x] Error handling in place

## See Also

- [Testing Guide](testing.md)
- [PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
