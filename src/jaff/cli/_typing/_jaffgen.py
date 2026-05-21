from pathlib import Path
from typing import TypedDict

from ...core import NetworkProps

JaffgenProps = TypedDict(
    "JaffgenProps",
    {
        "config_file": Path | None,
        "config_file_dir": Path | None,
        "output_dir": Path,
        "input_dir": Path | None,
        "input_files": list[Path] | None,
        "network_file": Path,
        "network_dir": Path,  # Used to override self.network_dir
        "default_lang": str | None,
        "template": str | None,
        "netprops": NetworkProps,
    },
)
