"""
Type definitions for indexed expressions in code generation.

This module provides data structures for representing indexed mathematical
expressions and collections thereof, used primarily in the Codegen class
for organizing CSE (common subexpression elimination) results and array
assignments.
"""

from functools import cached_property
from typing import Any, Iterable

from .core.logger import JaffLogger


class IndexedValue(tuple):
    """
    Immutable container for an indexed value with multi-dimensional indexing.

    Represents a value associated with one or more array indices, typically
    used for generating array assignment statements like:
        array[i][j] = expression

    This is an immutable tuple subclass with named properties for clarity.

    Attributes:
        indices: List of integer indices (e.g., [0], [2, 3], etc.)
        value: The value/expression associated with these indices

    Example:
        >>> iv = IndexedValue([0], "x + y")
        >>> iv.indices
        [0]
        >>> iv.value
        'x + y'
        >>> iv = IndexedValue([2, 3], "sin(theta)")  # For 2D array
    """

    def __new__(cls, indices: list[int], value: Any):
        """
        Create a new IndexedValue.

        Args:
            indices: List of integer indices for array access
            value: The value/expression to associate with these indices

        Raises:
            TypeError: If indices is not a list
        """
        if not isinstance(indices, list):
            raise TypeError(
                f"{indices}: indices must be of type list\n"
                f"Current index type detected: {type(indices)}"
            )
        return super().__new__(cls, (indices, value))

    @cached_property
    def indices(self) -> list[int]:
        """Get the list of indices."""
        return self[0]

    @cached_property
    def value(self) -> Any:
        """Get the associated value/expression."""
        return self[1]

    def __repr__(self):
        return f"IndexedValue(indices={self.indices!r}, value={self.value!r})"

    def __str__(self):
        if isinstance(self.value, list):
            value_str = "[" + ", ".join(str(v) for v in self.value) + "]"
        else:
            value_str = str(self.value)

        return f"{self.indices} -> {value_str}"


class IndexedList(list):
    """
    Type-safe list that only accepts IndexedValue elements.

    Provides a specialized list container ensuring all elements are
    IndexedValue instances, used to collect indexed expressions for
    code generation.

    Example:
        >>> items = IndexedList()
        >>> items.append(IndexedValue([0], "2*x"))
        >>> items.append(IndexedValue([1], "y**2"))
        >>> len(items)
        2
    """

    def __init__(
        self,
        items: Iterable | None = None,
        nested: bool = False,
        flatten: bool = False,
    ):
        """
        Initialize an IndexedList from an iterable.

        Args:
            items: Optional iterable to convert to IndexedList. If None, creates empty list.
                Can contain IndexedValue objects or raw values to be wrapped.
            nested: If True, nested iterables will be preserved in IndexedValue.value
                as nested structures. Cannot be used with flatten=True.
            flatten: If True, nested iterables will be flattened with multi-dimensional
                indices (e.g., [0, 1] for nested element). Cannot be used with nested=True.

        Raises:
            ValueError: If both nested=True and flatten=True
            TypeError: If items contain a mix of IndexedValue and non-IndexedValue objects

        Example:
            >>> IndexedList([1, 2, 3])  # Creates IndexedValue objects with single indices
            >>> IndexedList([[1, 2], [3, 4]], flatten=True)  # Flattens with 2D indices
            >>> IndexedList([[1, 2], [3, 4]], nested=True)  # Preserves nested structure
        """
        self.logger = JaffLogger().get_logger()
        if flatten and nested:
            raise ValueError("Cannot have both nested=True and flatten=True")

        if items is None:
            items = []

        # if not isinstance(items, list):
        items = list(items)

        if flatten:
            flat: list[IndexedValue] = []
            self.__convert_to_indexed_list(
                items,
                nested=nested,
                flatten=True,
                index_prefix=[],
                out=flat,
            )
            items = flat
        else:
            self.__convert_to_indexed_list(
                items,
                nested=nested,
                flatten=False,
                index_prefix=[],
            )

        super().__init__(items)

    def __repr__(self):
        return f"IndexedList({list.__repr__(self)})"

    def __str__(self):
        return "IndexedList[\n" + "\n".join(str(x) for x in self) + "\n]"

    def append(self, item: IndexedValue):
        """
        Append an IndexedValue to the list.

        Args:
            item: IndexedValue to append

        Raises:
            TypeError: If item is not an IndexedValue

        Warning:
            This method returns None (standard Python list behavior).
            Do NOT assign the return value:
                WRONG: out = out.append(item)  # out becomes None!
                RIGHT: out.append(item)         # out is modified in-place

        Example:
            >>> lst = IndexedList()
            >>> lst.append(IndexedValue([0], "value"))
            >>> len(lst)
            1
        """
        if not isinstance(item, IndexedValue):
            raise TypeError(f"{item} must be of type IndexedValue")

        super().append(item)

    def extend(self, items: Iterable[IndexedValue]):
        """
        Extend the list with multiple IndexedValue objects.

        Args:
            items: Iterable of IndexedValue objects

        Raises:
            TypeError: If any item is not an IndexedValue

        Warning:
            This method returns None (standard Python list behavior).
            Do NOT assign the return value:
                WRONG: out = out.extend(items)  # out becomes None!
                RIGHT: out.extend(items)         # out is modified in-place

        Example:
            >>> lst = IndexedList()
            >>> lst.extend([IndexedValue([0], "a"), IndexedValue([1], "b")])
            >>> len(lst)
            2
        """
        if any(not isinstance(item, IndexedValue) for item in items):
            raise TypeError(f"All items are not of type IndexedValue in: {items}")

        super().extend(items)

    @staticmethod
    def __is_iterable(obj: Any) -> bool:
        """
        Check if an object is iterable (but not a string).

        Args:
            obj: Object to check

        Returns:
            True if obj is iterable and not a string, False otherwise
        """
        return isinstance(obj, Iterable) and not isinstance(obj, (str, bytes))

    def __convert_to_indexed_list(
        self,
        items: list[Any],
        nested: bool,
        flatten: bool,
        index_prefix: list[int],
        out: list[IndexedValue] | None = None,
    ) -> None:
        """
        Recursively convert items to IndexedValue objects.

        This method handles conversion of raw values to IndexedValue objects,
        supporting both nested and flattened structures.

        Args:
            items: List of items to convert (modified in-place unless flatten=True)
            nested: If True, preserve nested iterables in IndexedValue.value
            flatten: If True, flatten nested structures with multi-dimensional indices
            index_prefix: Current index path for nested structures (used with flatten)
            out: Output list for flattened results (used only when flatten=True)
        """
        any_indexed = any(isinstance(x, IndexedValue) for x in items)
        all_indexed = all(isinstance(x, IndexedValue) for x in items)

        if any_indexed and not all_indexed:
            raise TypeError(
                "Items must be either ALL IndexedValue or NONE IndexedValue\n"
                f"{[(item, type(item)) for item in items]}"
            )

        if all_indexed:
            # Normalize IndexedValue objects to ensure nested iterables are IndexedList
            for i, item in enumerate(items):
                if isinstance(item, IndexedValue) and self.__is_iterable(item.value):
                    # Check if the iterable contains IndexedValue objects
                    if any(isinstance(v, IndexedValue) for v in item.value):
                        # Convert to IndexedList (handles list, tuple, etc.)
                        if not isinstance(item.value, IndexedList):
                            items[i] = IndexedValue(item.indices, IndexedList(item.value))
            if flatten and out is not None:
                out.extend(items)
            return

        for i, item in enumerate(items):
            idx = index_prefix + [i] if flatten else [i]

            if self.__is_iterable(item) and not isinstance(item, (str, bytes)):
                if flatten:
                    self.__convert_to_indexed_list(
                        item,
                        nested=nested,
                        flatten=True,
                        index_prefix=idx,
                        out=out,
                    )
                elif nested:
                    self.__convert_to_indexed_list(
                        item,
                        nested=nested,
                        flatten=False,
                        index_prefix=[],
                        out=None,
                    )
                    # Wrap the nested list in an IndexedList
                    items[i] = IndexedValue(idx, IndexedList(item))
                else:
                    items[i] = IndexedValue(idx, item)
            else:
                iv = IndexedValue(idx, item)
                if flatten and out is not None:
                    out.append(iv)
                else:
                    items[i] = iv

    def type(self) -> str:
        """
        Detect whether the IndexedList is 'normal', 'nested', or 'flattened'.

        Returns:
            str: One of 'normal', 'nested', or 'flattened'
                - 'flattened': Any IndexedValue has multi-dimensional indices (len > 1)
                - 'nested': Any IndexedValue has an iterable value containing IndexedValue objects
                - 'normal': All IndexedValues have single indices and values without nested IndexedValues

        Example:
            >>> lst = IndexedList([1, 2, 3])
            >>> lst.type()
            'normal'
            >>> lst = IndexedList([[1, 2], [3, 4]], nested=True)
            >>> lst.type()
            'nested'
            >>> lst = IndexedList([[1, 2], [3, 4]], flatten=True)
            >>> lst.type()
            'flattened'
        """
        if not self:
            return "normal"

        # Check for flattened: any multi-dimensional indices
        has_multidim_indices = any(len(item.indices) > 1 for item in self)
        if has_multidim_indices:
            return "flattened"

        # Check for nested: any iterable values containing IndexedValue objects
        for item in self:
            if self.__is_iterable(item.value):
                # Check if the iterable contains IndexedValue objects
                if any(isinstance(v, IndexedValue) for v in item.value):
                    return "nested"

        return "normal"

    def __normal_to_nested(self) -> "IndexedList":
        """Convert normal list to nested format."""
        # Normal with iterable values: convert to nested format
        # by wrapping list items in IndexedValue objects
        result = []
        for item in self:
            if self.__is_iterable(item.value):
                # Convert to list if needed
                nested_val = (
                    list(item.value) if not isinstance(item.value, list) else item.value
                )
                # Wrap each item in the list with IndexedValue
                nested_indexed_vals = []
                for i, val in enumerate(nested_val):
                    nested_indexed_vals.append(IndexedValue([i], val))
                # Wrap the list of IndexedValues in an IndexedList
                result.append(
                    IndexedValue(item.indices, IndexedList(nested_indexed_vals))
                )
            else:
                result.append(item)
        return IndexedList(result)

    def __normal_to_flattened(self) -> "IndexedList":
        """Convert normal list to flattened format."""
        result = []

        def flatten_recursive(item: IndexedValue, prefix_indices: list[int]) -> None:
            """Recursively flatten an IndexedValue."""
            if self.__is_iterable(item.value):
                for i, sub_item in enumerate(item.value):
                    new_indices = prefix_indices + [i]
                    if isinstance(sub_item, IndexedValue):
                        # Nested IndexedValue: combine indices
                        flatten_recursive(sub_item, new_indices)
                    elif self.__is_iterable(sub_item):
                        # Nested iterable: recurse
                        flatten_recursive(IndexedValue([i], sub_item), prefix_indices)
                    else:
                        # Leaf value
                        result.append(IndexedValue(new_indices, sub_item))
            else:
                # Non-iterable value
                result.append(IndexedValue(prefix_indices, item.value))

        for item in self:
            flatten_recursive(item, item.indices)

        return IndexedList(result)

    def __nested_to_normal(self) -> "IndexedList":
        """Convert nested list to normal format by reconstructing list values from IndexedValues."""
        result = []

        for i, item in enumerate(self):
            if self.__is_iterable(item.value):
                # Check if it contains IndexedValue objects
                has_indexed_values = any(isinstance(v, IndexedValue) for v in item.value)
                if has_indexed_values:
                    # Reconstruct as a regular list from IndexedValues
                    reconstructed = []
                    for indexed_val in item.value:
                        if isinstance(indexed_val, IndexedValue):
                            reconstructed.append(indexed_val.value)
                        else:
                            reconstructed.append(indexed_val)
                    result.append(IndexedValue([i], reconstructed))
                else:
                    # Regular iterable value (not nested IndexedValues), keep as is
                    result.append(IndexedValue([i], item.value))
            else:
                result.append(IndexedValue([i], item.value))

        return IndexedList(result)

    def __nested_to_flattened(self) -> "IndexedList":
        """Convert nested list to flattened format."""
        result = []

        def flatten_recursive(item: IndexedValue, prefix_indices: list[int]) -> None:
            """Recursively flatten an IndexedValue."""
            if self.__is_iterable(item.value):
                for i, sub_item in enumerate(item.value):
                    new_indices = prefix_indices + [i]
                    if isinstance(sub_item, IndexedValue):
                        # Nested IndexedValue: combine indices
                        flatten_recursive(sub_item, new_indices)
                    elif self.__is_iterable(sub_item):
                        # Nested iterable: recurse
                        flatten_recursive(IndexedValue([i], sub_item), prefix_indices)
                    else:
                        # Leaf value
                        result.append(IndexedValue(new_indices, sub_item))
            else:
                # Non-iterable value
                result.append(IndexedValue(prefix_indices, item.value))

        for item in self:
            flatten_recursive(item, item.indices)

        return IndexedList(result)

    def __flattened_to_normal(self) -> "IndexedList":
        """Convert flattened list to normal format by reconstructing nested structures as list values."""
        from collections import defaultdict

        # Group by first index
        grouped = defaultdict(list)
        for item in self:
            first_idx = item.indices[0]
            remaining_indices = item.indices[1:]
            grouped[first_idx].append((remaining_indices, item.value))

        result = []
        for idx in sorted(grouped.keys()):
            items_at_idx = grouped[idx]

            if len(items_at_idx) == 1 and not items_at_idx[0][0]:
                # Single item with no remaining indices - keep as simple value
                result.append(IndexedValue([idx], items_at_idx[0][1]))
            else:
                # Multiple items or items with remaining indices - reconstruct as list
                reconstructed = []
                for remaining_idx, value in sorted(items_at_idx, key=lambda x: x[0]):
                    reconstructed.append(value)
                result.append(IndexedValue([idx], reconstructed))

        return IndexedList(result)

    def __flattened_to_nested(self) -> "IndexedList":
        """Convert flattened list to nested format."""
        from collections import defaultdict

        grouped = defaultdict(list)

        for item in self:
            first_idx = item.indices[0]
            remaining_indices = item.indices[1:]
            grouped[first_idx].append((remaining_indices, item.value))

        result = []
        for idx in sorted(grouped.keys()):
            items_at_idx = grouped[idx]

            # If only one item with no remaining indices, keep as scalar value
            if len(items_at_idx) == 1 and not items_at_idx[0][0]:
                result.append(IndexedValue([idx], items_at_idx[0][1]))
            else:
                # Create nested structure with IndexedValues
                nested_values = []
                for remaining_idx, value in items_at_idx:
                    if remaining_idx:  # Still has indices, create IndexedValue
                        nested_values.append(IndexedValue(remaining_idx, value))
                    else:
                        nested_values.append(value)
                # Wrap the list of IndexedValues in an IndexedList
                result.append(IndexedValue([idx], IndexedList(nested_values)))

        return IndexedList(result)

    def nested(self) -> "IndexedList":
        """
        Convert the IndexedList to nested format.

        Returns:
            IndexedList: New IndexedList in nested format

        Raises:
            ValueError: If conversion to nested is not possible

        Example:
            >>> lst = IndexedList([[1, 2], [3, 4]], flatten=True)
            >>> nested = lst.nested()
            >>> nested.type()
            'nested'
        """
        list_type = self.type()

        # If already nested, return a copy
        if list_type == "nested":
            return IndexedList(list(self))

        # Convert from normal
        if list_type == "normal":
            if not any(self.__is_iterable(item.value) for item in self):
                self.logger.warning(
                    "Cannot convert to nested format: no iterable values. Returning copy."
                )
                return IndexedList(list(self))
            return self.__normal_to_nested()

        # Convert from flattened
        if list_type == "flattened":
            return self.__flattened_to_nested()

        # Should never reach here
        raise ValueError(f"Unknown list type: {list_type}")

    def flatten(self) -> "IndexedList":
        """
        Convert the IndexedList to flattened format.

        Returns:
            IndexedList: New IndexedList in flattened format

        Raises:
            ValueError: If conversion to flattened is not possible

        Example:
            >>> lst = IndexedList([[1, 2], [3, 4]], nested=True)
            >>> flat = lst.flatten()
            >>> flat.type()
            'flattened'
        """
        list_type = self.type()

        # If already flattened, return a copy
        if list_type == "flattened":
            return IndexedList(list(self))

        # Convert from normal
        if list_type == "normal":
            if not any(self.__is_iterable(item.value) for item in self):
                self.logger.warning(
                    "Cannot convert to flattened format: no iterable values. Returning copy."
                )
                return IndexedList(list(self))
            return self.__normal_to_flattened()

        # Convert from nested
        if list_type == "nested":
            return self.__nested_to_flattened()

        # Should never reach here
        raise ValueError(f"Unknown list type: {list_type}")

    def normal(self) -> "IndexedList":
        """
        Convert the IndexedList to normal format.

        Returns:
            IndexedList: New IndexedList in normal format

        Raises:
            ValueError: If conversion to normal is not possible

        Example:
            >>> lst = IndexedList([[1], [2]], nested=True)
            >>> normal = lst.normal()
            >>> normal.type()
            'normal'
        """
        list_type = self.type()

        # If already normal, return a copy
        if list_type == "normal":
            return IndexedList(list(self))

        # Convert from flattened
        if list_type == "flattened":
            return self.__flattened_to_normal()

        # Convert from nested
        if list_type == "nested":
            return self.__nested_to_normal()

        # Should never reach here
        raise ValueError(f"Unknown list type: {list_type}")
