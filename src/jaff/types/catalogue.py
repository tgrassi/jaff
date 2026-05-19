class Catalogue:
    def __init__(self):
        self._map = {}
        self._list = []

    def __getitem__(self, key: str | int):
        if isinstance(key, str):
            if key not in self._map:
                raise KeyError(f"{key}' not found in catalogue")
            return self._map[key]

        elif isinstance(key, (int, slice)):
            return self._list[key]

        raise TypeError("Catalogue key must be a string or integer")

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self._map
        return item in self._list
