---
tags:
    - Api
    - Types
icon: lucide/square-chart-gantt
---

# JAFF Types

The `jaff_types` module provides specialized data structures for representing indexed mathematical expressions and collections used in code generation.

## Overview

This module defines two primary classes that work together to organize and structure code generation output:

- **`IndexedValue`** - An immutable container representing a value associated with array indices
- **`IndexedList`** - A type-safe list that only accepts `IndexedValue` elements

These types are used extensively in the `Codegen` class to structure CSE (Common Subexpression Elimination) results, array assignments, and other indexed expressions.

```python
from jaff.jaff_types import IndexedValue, IndexedList

# Create an indexed value
iv = IndexedValue([0], "x + y")
print(iv.indices)  # [0]
print(iv.value)    # "x + y"

# Create a list of indexed values
items = IndexedList([
    IndexedValue([0], "2*x"),
    IndexedValue([1], "y**2")
])
```

---

## Classes

### IndexedValue

```python
class IndexedValue(tuple):
    """
    Immutable container for an indexed value with multi-dimensional indexing.
    """
```

An immutable tuple subclass that pairs one or more array indices with a value or expression. Used to represent statements like `array[i] = expression` or `matrix[i][j] = expression`.

#### Constructor

##### `IndexedValue()`

Create a new IndexedValue.

**Parameters:**

- `indices` (list\[int\]): List of integer indices for array access (e.g., `[0]`, `[2, 3]`)
- `value` (Any): The value/expression to associate with these indices

**Returns:**

- `IndexedValue`: New indexed value instance

**Raises:**

- `TypeError`: If `indices` is not a list

**Examples:**

```python
# 1D array indexing
iv1 = IndexedValue([0], "x + y")
# Represents: array[0] = x + y

# 2D array indexing
iv2 = IndexedValue([2, 3], "sin(theta)")
# Represents: matrix[2][3] = sin(theta)

# Complex expression
iv3 = IndexedValue([5], "k[0] * n[1] * n[2]")
# Represents: rate[5] = k[0] * n[1] * n[2]
```

#### Properties

##### `indices`

```python
@property
def indices(self) -> list[int]
```

Get the list of integer indices.

**Returns:**

- `list[int]`: List of indices

**Example:**

```python
iv = IndexedValue([2, 3], "value")
print(iv.indices)  # [2, 3]
```

##### `value`

```python
@property
def value(self) -> Any
```

Get the associated value or expression.

**Returns:**

- `Any`: The value/expression (can be string, number, list, etc.)

**Example:**

```python
iv = IndexedValue([0], "x + y")
print(iv.value)  # "x + y"

iv2 = IndexedValue([1], [1, 2, 3])
print(iv2.value)  # [1, 2, 3]
```

#### Methods

##### `__repr__()`

Return detailed string representation.

**Returns:**

- `str`: String representation showing both indices and value

**Example:**

```python
iv = IndexedValue([0], "x + y")
print(repr(iv))
# Output: IndexedValue(indices=[0], value='x + y')
```

##### `__str__()`

Return human-readable string representation.

**Returns:**

- `str`: Formatted string showing indices → value mapping

**Example:**

```python
iv = IndexedValue([0], "x + y")
print(str(iv))
# Output: [0] -> x + y

iv2 = IndexedValue([1], [1, 2, 3])
print(str(iv2))
# Output: [1] -> [1, 2, 3]
```

#### Immutability

`IndexedValue` is immutable (inherits from `tuple`), so indices and values cannot be changed after creation:

```python
iv = IndexedValue([0], "value")
# iv.indices[0] = 1  # Would raise error - tuples are immutable
# iv.value = "new"   # Would raise error - no setter defined

# To "modify", create a new IndexedValue:
iv_modified = IndexedValue([1], "new_value")
```

---

### IndexedList

```python
class IndexedList(list):
    """
    Type-safe list that only accepts IndexedValue elements.
    """
```

A specialized list container ensuring all elements are `IndexedValue` instances. Provides automatic conversion from various input formats and supports nested/flattened representations.

#### Constructor

##### `IndexedList()`

Initialize an IndexedList from an iterable.

**Parameters:**

- `items` (Iterable | None): Optional iterable to convert to IndexedList
    - If `None`, creates empty list
    - Can contain `IndexedValue` objects or raw values to be wrapped
    - Nested iterables are handled based on `nested` and `flatten` flags
- `nested` (bool): If `True`, preserve nested iterables in `IndexedValue.value` as `IndexedList` structures. Default: `False`
    - Cannot be used with `flatten=True`
- `flatten` (bool): If `True`, flatten nested iterables with multi-dimensional indices. Default: `False`
    - Cannot be used with `nested=True`

**Returns:**

- `IndexedList`: New indexed list instance

**Raises:**

- `ValueError`: If both `nested=True` and `flatten=True`
- `TypeError`: If items contain a mix of `IndexedValue` and non-`IndexedValue` objects

**Examples:**

```python
# From simple values
items = IndexedList([1, 2, 3])
# Creates: [IndexedValue([0], 1), IndexedValue([1], 2), IndexedValue([2], 3)]

# From existing IndexedValue objects
iv1 = IndexedValue([0], "x")
iv2 = IndexedValue([1], "y")
items = IndexedList([iv1, iv2])

# Nested structure - preserved
nested_items = IndexedList([[1, 2], [3, 4]], nested=True)
# Creates: [
#   IndexedValue([0], IndexedList([IndexedValue([0], 1), IndexedValue([1], 2)])),
#   IndexedValue([1], IndexedList([IndexedValue([0], 3), IndexedValue([1], 4)]))
# ]

# Nested structure - flattened with 2D indices
flat_items = IndexedList([[1, 2], [3, 4]], flatten=True)
# Creates: [
#   IndexedValue([0, 0], 1),
#   IndexedValue([0, 1], 2),
#   IndexedValue([1, 0], 3),
#   IndexedValue([1, 1], 4)
# ]

# Empty list
empty = IndexedList()
```

#### Methods

##### `append()`

Append an IndexedValue to the list.

**Parameters:**

- `item` (IndexedValue): IndexedValue to append

**Raises:**

- `TypeError`: If item is not an IndexedValue

**Example:**

```python
items = IndexedList()
items.append(IndexedValue([0], "value"))
# items.append("plain_value")  # Would raise TypeError
```

##### `extend()`

Extend the list with multiple IndexedValue objects.

**Parameters:**

- `items` (Iterable\[IndexedValue\]): Iterable of IndexedValue objects

**Raises:**

- `TypeError`: If any item is not an IndexedValue

**Example:**

```python
items = IndexedList()
new_items = [
    IndexedValue([0], "x"),
    IndexedValue([1], "y")
]
items.extend(new_items)
```

##### `type()`

Determine the structure type of the IndexedList.

**Returns:**

- `str`: One of `"normal"`, `"nested"`, or `"flattened"`
    - `"normal"`: All IndexedValue objects have single-element indices and non-iterable values
    - `"nested"`: All IndexedValue objects have single-element indices and IndexedList values
    - `"flattened"`: All IndexedValue objects have multi-element indices

**Example:**

```python
normal = IndexedList([1, 2, 3])
print(normal.type())  # "normal"

nested = IndexedList([[1, 2], [3, 4]], nested=True)
print(nested.type())  # "nested"

flat = IndexedList([[1, 2], [3, 4]], flatten=True)
print(flat.type())  # "flattened"
```

##### `nested()`

Convert to nested representation.

**Returns:**

- `IndexedList`: New IndexedList with nested structure (type="nested")

**Example:**

```python
flat = IndexedList([[1, 2], [3, 4]], flatten=True)
# [IndexedValue([0, 0], 1), IndexedValue([0, 1], 2), ...]

nested = flat.nested()
# [IndexedValue([0], IndexedList([...])), IndexedValue([1], IndexedList([...]))]
```

##### `flatten()`

Convert to flattened representation.

**Returns:**

- `IndexedList`: New IndexedList with flattened structure (type="flattened")

**Example:**

```python
nested = IndexedList([[1, 2], [3, 4]], nested=True)
flat = nested.flatten()
# [IndexedValue([0, 0], 1), IndexedValue([0, 1], 2), ...]
```

##### `normal()`

Convert to normal representation (single indices, simple values).

**Returns:**

- `IndexedList`: New IndexedList with normal structure (type="normal")

**Note:**

For flattened multi-dimensional lists, this extracts the innermost values and re-indexes sequentially.

**Example:**

```python
flat = IndexedList([[1, 2], [3, 4]], flatten=True)
normal = flat.normal()
# [IndexedValue([0], 1), IndexedValue([1], 2), IndexedValue([2], 3), IndexedValue([3], 4)]
```

##### `__repr__()`

Return detailed string representation.

**Returns:**

- `str`: String representation showing all IndexedValue objects

##### `__str__()`

Return formatted string representation.

**Returns:**

- `str`: Multi-line formatted string with one IndexedValue per line

**Example:**

```python
items = IndexedList([1, 2, 3])
print(items)
# Output:
# IndexedList[
# [0] -> 1
# [1] -> 2
# [2] -> 3
# ]
```

---

## Usage in Code Generation

### CSE (Common Subexpression Elimination)

The `Codegen` class returns `IndexedList` objects containing CSE temporaries:

```python
from jaff import Network, Codegen

net = Network("networks/react_COthin")
cg = Codegen(network=net, lang="cxx")

# Get indexed rates with CSE
result = cg.get_indexed_rates(use_cse=True, cse_var="cse")

# Access CSE temporaries (IndexedList)
cse_temps = result["extras"]["cse"]
for iv in cse_temps:
    print(f"cse[{iv.indices[0]}] = {iv.value}")
# Output:
# cse[0] = sqrt(tgas)
# cse[1] = exp(-500/tgas)
# ...

# Access rate expressions (IndexedList)
rates = result["expressions"]
for iv in rates:
    print(f"k[{iv.indices[0]}] = {iv.value}")
# Output:
# k[0] = 1.2e-10 * cse[0]
# k[1] = 3.4e-11 * cse[1]
# ...
```

### Multi-Dimensional Indexing

For Jacobian matrices and other 2D structures:

```python
# Get indexed Jacobian
result = cg.get_indexed_jacobian(use_cse=True)

# Jacobian elements (flattened)
jac_elements = result["expressions"]
for iv in jac_elements:
    i, j = iv.indices  # 2D indices
    print(f"jac[{i}][{j}] = {iv.value}")
# Output:
# jac[0][0] = -k[0]*n[1]
# jac[0][1] = -k[0]*n[0]
# jac[1][0] = k[1]*n[2]
# ...

# Convert to nested representation
nested_jac = jac_elements.nested()
for iv in nested_jac:
    row_idx = iv.indices[0]
    row_elements = iv.value  # IndexedList of column elements
    print(f"Row {row_idx}: {len(row_elements)} elements")
```

### Type Checking

```python
from jaff.jaff_types import IndexedValue, IndexedList

def process_indexed_list(items: IndexedList) -> None:
    """Process an IndexedList safely."""
    if not isinstance(items, IndexedList):
        raise TypeError("Expected IndexedList")

    for item in items:
        if not isinstance(item, IndexedValue):
            raise TypeError("All items must be IndexedValue")

        # Process item
        print(f"Index {item.indices}: {item.value}")

# Usage with Codegen results
result = cg.get_indexed_rates()
process_indexed_list(result["expressions"])
```

---

## Type Conversions

### Normal ↔ Nested ↔ Flattened

```python
# Start with nested structure
data = [[1, 2], [3, 4], [5, 6]]

# Create in different formats
normal = IndexedList(data)       # Default: normal (unnested)
nested = IndexedList(data, nested=True)
flat = IndexedList(data, flatten=True)

# Convert between formats
print(normal.type())    # "normal"
print(nested.type())    # "nested"
print(flat.type())      # "flattened"

# Conversion examples
flat_from_nested = nested.flatten()
normal_from_flat = flat.normal()
nested_from_flat = flat.nested()

# All conversions preserve data
assert len(flat_from_nested) == 6  # 2*3 flattened elements
```

### Integration with Codegen Methods

Methods returning `IndexedReturn`:

| Method                 | Returns CSE      | Returns Expressions |
| ---------------------- | ---------------- | ------------------- |
| `get_indexed_rates`    | IndexedList (1D) | IndexedList (1D)    |
| `get_indexed_odes`     | IndexedList (1D) | IndexedList (1D)    |
| `get_indexed_rhs`      | IndexedList (1D) | IndexedList (1D)    |
| `get_indexed_jacobian` | IndexedList (1D) | IndexedList (2D)    |

```python
from jaff.codegen import IndexedReturn

# Type annotation for method return
def get_expressions(cg: Codegen) -> IndexedReturn:
    result: IndexedReturn = cg.get_indexed_rates(use_cse=True)

    # Access typed components
    cse: IndexedList = result["extras"]["cse"]
    exprs: IndexedList = result["expressions"]

    return result
```

---

## See Also

- [Codegen API](codegen.md) - Code generation methods that use these types
- [File Parser API](file-parser.md) - Template parser utilizing indexed types
- [Code Generation Guide](../user-guide/code-generation.md) - Using generated indexed expressions
