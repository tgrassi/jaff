from typing import Generic, Iterator, TypeVar

T = TypeVar("T")


class Catalogue(Generic[T]):
    def __init__(
        self, items: list[T] | None = None, items_dict: dict[str, T] | None = None
    ):
        if (items is None) ^ (items_dict is None):
            raise ValueError("Both an list and a dict must be supplied")

        if items is not None and items_dict is not None:
            if len(items) != len(items_dict.keys()):
                raise ValueError("Length of both list and dict must be same")

        self._by_name: dict[str, T] = {} if items_dict is None else items_dict
        self._list: list[T] = [] if items is None else items
        self._by_serialized: dict[str, T] = {}  # Items must be manually added

    def __getitem__(self, key: str | int) -> T:
        if isinstance(key, str):
            if key not in self._by_name and key not in self._by_serialized:
                raise KeyError(f"{key}' not found in catalogue")

            if key in self._by_name:
                return self._by_name[key]

            if key in self._by_serialized:
                return self._by_serialized[key]

        elif isinstance(key, (int, slice)):
            return self._list[key]

        raise TypeError("Catalogue key must be a string or integer")

    def __iter__(self) -> Iterator[T]:
        return iter(self._list)

    def __len__(self) -> int:
        return len(self._list)

    def __contains__(self, item) -> bool:
        if isinstance(item, str):
            return item in self._by_name or item in self._by_serialized

        return item in self._list
