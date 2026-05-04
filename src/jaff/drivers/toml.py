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
        with open(self.file, "rb") as f:
            data = tomllib.load(f)

        return data

    def get_key(self, key) -> Any:
        return self.data.get(key, None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.file
