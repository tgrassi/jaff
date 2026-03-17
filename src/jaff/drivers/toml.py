from pathlib import Path
from typing import Any

import tomllib


class Toml:
    def __init__(self, file: str | Path):
        if isinstance(file, str):
            file = Path(file)

        self.file = file
        self.data = self.__get_dict()

    def __get_dict(self) -> dict:
        data = {}
        with open(self.file, "rb") as f:
            data = tomllib.load(f)

        return data

    def get_key(self, key) -> Any:
        return self.data.get(key, None)
