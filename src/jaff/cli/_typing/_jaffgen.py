"""
TypedDict definitions for the ``jaffgen`` CLI configuration state.

This module declares :class:`JaffgenProps`, a :class:`typing.TypedDict` that
holds the fully-resolved runtime configuration assembled by
:class:`~jaff.cli.JaffGen` during argument parsing.  It is used as the type
annotation for ``JaffGen.jaffgen_config``.

The dictionary is populated progressively:

1. ``config_file`` / ``config_file_dir`` are set first (may remain ``None``).
2. ``input_dir``, ``input_files``, ``template`` are filled in from CLI args or
   the TOML config.
3. ``network_file``, ``output_dir``, ``default_lang`` are resolved last.
4. ``netprops`` accumulates the keyword arguments forwarded to the
   :class:`~jaff.Network` constructor.
"""

from pathlib import Path
from typing import TypedDict

from ...core import NetworkProps


class JaffgenProps(TypedDict):
    """
    Fully-resolved runtime configuration for a ``jaffgen`` invocation.

    This typed dictionary is the single source of truth for all paths and
    settings assembled from CLI arguments, TOML config, and built-in
    defaults during a ``jaffgen`` run.

    Keys
    ----
    config_file : Path or None
        Absolute path to the loaded ``jaff.toml`` configuration file, or
        ``None`` if no config file was found or specified.
    config_file_dir : Path or None
        Directory containing ``config_file``; used to resolve relative paths
        declared inside the TOML config.  ``None`` when no config file is
        present.
    output_dir : Path
        Absolute path to the directory where generated output files are
        written.
    input_dir : Path or None
        Absolute path to a directory of template files to process, or
        ``None`` if ``--indir`` was not supplied.
    input_files : list of Path or None
        Absolute paths of individually specified template files (from
        ``--files``), or ``None`` if that flag was not used.
    network_file : Path
        Absolute path to the ``.jet`` chemical reaction network file.
    network_dir : Path
        Override for the built-in ``networks/`` directory.  Rarely needed
        outside of testing or alternative installation layouts.
    default_lang : str or None
        Default programming language token (e.g. ``"c"``, ``"python"``)
        applied to template files whose extension is not recognised.
        ``None`` means the template parser must infer the language itself.
    template : str or None
        Name of the selected built-in template collection (subdirectory
        inside ``jaff/templates/generator/``), or ``None`` if no template
        was requested.
    netprops : NetworkProps
        Keyword arguments forwarded verbatim to the :class:`~jaff.Network`
        constructor.  Assembled from CLI flags, TOML ``[network]`` entries,
        and :class:`~jaff.Network` parameter defaults.
    """

    config_file: Path | None
    config_file_dir: Path | None
    output_dir: Path
    input_dir: Path | None
    input_files: list[Path] | None
    network_file: Path
    network_dir: Path  # Used to override self.network_dir
    default_lang: str | None
    template: str | None
    netprops: NetworkProps
