"""
JAFF Code Generator CLI Interface.

This module provides the ``jaffgen`` command-line entry point for the JAFF
(Just Another Fancy Format) code generator.  It reads one or more template
files that contain JAFF directives, resolves a chemical reaction network, and
writes language-specific source files (C, C++, Fortran, Python, Rust, Julia,
or R) to an output directory.

Configuration can come from three sources, applied with the following priority
order (highest → lowest):

1. Explicit CLI argument (e.g. ``--network``)
2. Values in a ``jaff.toml`` config file (``--config`` or auto-detected inside
   the template directory)
3. Hard-coded defaults on the :class:`~jaff.Network` constructor

Template lookup
---------------
Built-in templates live inside ``jaff/templates/generator/<name>/`` and
``jaff/templates/preprocessor/<name>/``.  When ``--template <name>`` is
given, all files from the *generator* subdirectory are collected first; any
preprocessor file whose name does not clash with a generator file is appended
afterwards, so the generator always wins on name collisions.

Usage
-----
::

    jaffgen --network networks/react_COthin [--outdir <dir>] [--indir <dir>]
            [--files <file> ...] [--template <name>] [--lang <lang>]

Examples
--------
::

    # Generate code from a specific template directory
    jaffgen --network networks/react_COthin --indir templates/ --outdir output/

    # Use a predefined template collection
    jaffgen --network networks/react_COthin --template my_template --outdir output/

    # Process specific files with a default language
    jaffgen --network networks/test.dat --files file1.txt file2.txt --lang rust
"""

from __future__ import annotations

import argparse
from inspect import signature
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from .. import Network
from ..cli import ConfigTable
from ..codegen import Codegen as cg
from ..codegen import TemplateParser
from ..common import motd
from ..drivers import HDF5, Toml
from ..io import JaffLogger, jaff_progress
from ..types import HDF5Dict
from ._typing import JaffgenProps

if TYPE_CHECKING:
    import logging


class JaffGen:
    """
    Entry-point class for the ``jaffgen`` CLI command.

    Instantiating this class drives the full code-generation pipeline:

    1. Parse CLI arguments and (optionally) a ``jaff.toml`` config file.
    2. Resolve input template files from ``--indir``, ``--files``, or
       ``--template``.
    3. Load the chemical reaction network.
    4. Run :class:`~jaff.codegen.TemplateParser` on every template file and
       write the generated output to ``--outdir``.

    All private ``__set_*`` helpers follow the same resolution pattern:
    *CLI arg* takes priority over *config file* value; absent both, the
    corresponding :class:`~jaff.Network` constructor default is used.

    Parameters
    ----------
    None
        Arguments are read directly from ``sys.argv`` via
        :mod:`argparse`.

    Raises
    ------
    RuntimeError
        If no valid input file, folder, or template name is supplied, or if
        no network file is provided.
    FileNotFoundError
        If a specified config file, network file, input file/directory, or
        output path does not exist.
    NotADirectoryError
        If the resolved output path is not a directory.
    ValueError
        If an unsupported template name or programming language is given.
    """

    def __init__(self):
        """Drive the full ``jaffgen`` code-generation pipeline from CLI arguments.

        Reads arguments from ``sys.argv``, resolves configuration from a
        ``jaff.toml`` file when present, loads the chemical reaction network, and
        writes generated source files to the output directory.

        Raises
        ------
        RuntimeError
            If no valid input file, folder, or template name is supplied, or if
            no network file is provided.
        FileNotFoundError
            If a specified config file, network file, input file/directory, or
            output path does not exist.
        NotADirectoryError
            If the resolved output path is not a directory.
        ValueError
            If an unsupported template name or programming language is given.
        """
        print(motd("jaffgen"))
        self.parser: argparse.ArgumentParser = self.__get_parser()
        self.__set_parser_props()

        self.logger: logging.Logger = JaffLogger().get_logger()
        self.args: argparse.Namespace = self.parser.parse_args()

        # Locate JAFF package directory and built-in template directories.
        # Templates are stored inside jaff/templates/{generator,preprocessor}/.
        self.jaff_dir: Path = Path(__file__).parent.parent
        self.network_dir: Path = self.jaff_dir.parent.parent / "networks"
        self.generator_template_dir: Path = self.jaff_dir / "templates" / "generator"
        self.preprocessor_template_dir: Path = (
            self.jaff_dir / "templates" / "preprocessor"
        )
        self.files: list[Path] = []
        self.jaffgen_config: JaffgenProps = {"netprops": {}}  # type: ignore
        self.jaffgen_config_raw: Toml | None = None

        # Sentinel values — populated by __set_config if a config file is found.
        self.jaffgen_config["config_file"] = None
        self.jaffgen_config["config_file_dir"] = None

        # Phase 1: apply whatever inputs the user passed explicitly on the CLI.
        # These calls may leave fields as None if an argument was not provided.
        self.__set_config(self.args.config)
        self.__set_input_dir(self.args.indir)
        self.__set_input_files(self.args.files)
        self.__set_template(self.args.template)

        # Phase 2: look for a jaff.toml embedded inside the file list (only if
        # --config was not already given).
        self.__read_jaff_config_from_files()

        # Phase 3: fill in anything still missing from the config file.
        if not self.args.indir:
            self.__set_input_dir(self.__get_prop(None, "jaffgen", "input_dir"))
        if not self.args.files:
            self.__set_input_files(self.__get_prop(None, "jaffgen", "input_files"))
        if not self.args.template:
            self.__set_template(self.__get_prop(None, "jaffgen", "template"))

        # At least one template file must be resolvable before continuing.
        if not self.files:
            raise RuntimeError("No valid input file/folder/template have been supplied")

        # Phase 4: resolve remaining network / output settings, again preferring
        # the CLI arg and falling back to the config file.
        self.__set_network(self.__get_prop(self.args.network, "jaffgen", "network"))
        self.__set_output_dir(self.__get_prop(self.args.outdir, "jaffgen", "output_dir"))
        self.__set_default_lang(
            self.__get_prop(self.args.lang, "jaffgen", "default_lang")
        )

        # Collect the full set of Network constructor parameter signatures so
        # we can fall back to their defaults cleanly.
        self.network_params = signature(Network).parameters
        self.jaffgen_config["netprops"]["fname"] = self.jaffgen_config["network_file"]
        self.jaffgen_config["netprops"]["_from_cli"] = True
        self.__set_funcfile(self.__get_prop(self.args.funcfile, "network", "funcfile"))
        self.jaffgen_config["netprops"]["label"] = (
            self.__get_prop(self.args.label, "network", "label")
            or self.network_params["label"].default
        )

        replace_nh = self.__get_prop(self.args.replace_nH, "network", "replace_nH")
        self.jaffgen_config["netprops"]["replace_nH"] = (
            replace_nh
            if replace_nh is not None
            else self.network_params["replace_nH"].default
        )

        errors = self.__get_prop(self.args.errors, "network", "errors")
        self.jaffgen_config["netprops"]["errors"] = (
            errors if errors is not None else self.network_params["errors"].default
        )

        # Handle optional config-file-only sections.
        if self.jaffgen_config_raw:
            rad_props = self.jaffgen_config_raw.get_key("radiation")
            if rad_props:
                self.__handle_radiation(rad_props)

            table_props = self.jaffgen_config_raw.get_key("table")
            if table_props:
                self.__handle_data_tables(table_props)

        # Create the Network instance and immediately run code generation.
        self.net: Network = Network(**self.jaffgen_config["netprops"])
        self.__process_files()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def __get_prop(
        self, arg_prop: str | None, dict_key: str, dict_prop: str
    ) -> Any | None:
        """
        Resolve a configuration value from the CLI arg or config file.

        Returns *arg_prop* unchanged if it is not ``None``.  Otherwise looks
        the value up in the raw TOML config under ``[dict_key] / dict_prop``.

        Parameters
        ----------
        arg_prop : str or None
            Value provided on the command line (``None`` if absent).
        dict_key : str
            Top-level TOML section key (e.g. ``"jaffgen"`` or ``"network"``).
        dict_prop : str
            Key within that section (e.g. ``"input_dir"``).

        Returns
        -------
        Any or None
            The resolved value, or ``None`` if neither source has it.
        """
        return arg_prop or (
            (self.jaffgen_config_raw.get_key(dict_key) or {}).get(dict_prop, None)
            if self.jaffgen_config_raw is not None
            else None
        )

    def __set_config(self, config_file: str | Path | None) -> None:
        """
        Load a ``jaff.toml`` config file and store its parsed contents.

        Parameters
        ----------
        config_file : str, Path, or None
            Path to the TOML config file.  Does nothing if ``None``.

        Raises
        ------
        FileNotFoundError
            If *config_file* does not exist or is not a regular file.
        """
        if config_file is None:
            return

        if isinstance(config_file, str):
            config_file = Path(config_file)

        if not config_file.exists():
            raise FileNotFoundError(config_file)

        if not config_file.is_file():
            raise FileNotFoundError(f"{config_file} is not a file")

        self.jaffgen_config["config_file"] = config_file
        self.jaffgen_config["config_file_dir"] = config_file.parent
        # Parse the TOML file so downstream helpers can call get_key().
        self.jaffgen_config_raw = Toml(config_file)

    def __process_files(self) -> None:
        """
        Run the template parser on every resolved input file and write output.

        Iterates over ``self.files``, instantiates a
        :class:`~jaff.codegen.TemplateParser` for each, and writes the
        generated text to ``output_dir / <filename>``.

        Returns
        -------
        None
        """
        # Process each template file in turn, showing a progress bar.
        for file in jaff_progress.track(self.files, description="Processing files"):
            # Instantiate the parser for this single template.
            fparser: TemplateParser = TemplateParser(
                self.net, file, self.jaffgen_config["default_lang"]
            )

            # Generate the full output text for this file.
            lines: str = fparser.parse_file()

            # Write the generated code into the output directory, preserving
            # the original filename.
            outfile: Path = self.jaffgen_config["output_dir"] / file.name
            with open(outfile, "w") as f:
                f.write(lines)

            self.logger.info(
                f"[cyan]{file.name}[/] created at {self.jaffgen_config['output_dir']}"
            )

        self.logger.info("[green]Successfully generated files[/]")
        self.logger.info(
            f"Generated files can be found at {self.jaffgen_config['output_dir']}"
        )

    def __read_jaff_config_from_files(self) -> None:
        """
        Auto-detect a ``jaff.toml`` embedded within the collected file list.

        If ``--config`` was not given explicitly, scan the resolved file list
        for a file named ``jaff.toml`` and load it as the config file.  This
        allows template directories to ship their own config without requiring
        an extra ``--config`` flag.

        Returns
        -------
        None
        """
        # Only auto-detect if no explicit config was already loaded.
        if self.jaffgen_config["config_file"] is not None:
            return

        # Search for a jaff.toml among the already-collected template files.
        jaff_config_index: int | None = next(
            (i for i, f in enumerate(self.files) if f.name == "jaff.toml"), None
        )

        if jaff_config_index is not None:
            self.__set_config(self.files[jaff_config_index])

    def __set_template(self, template: str | None) -> None:
        """
        Resolve a named built-in template and collect its files.

        Looks up *template* inside ``jaff/templates/generator/``.  Generator
        files are always preferred; any preprocessor file whose name does not
        match an existing generator file is appended to ``self.files`` as a
        fallback.

        Parameters
        ----------
        template : str or None
            Name of the built-in template collection (subdirectory name).
            Does nothing if ``None``.

        Raises
        ------
        ValueError
            If *template* is not found in the generator templates directory.
        """
        if template is None:
            self.jaffgen_config["template"] = None
            return

        # List all subdirectory names inside templates/generator/ — each one
        # is a valid template collection name.
        generator_templates: list[str] = [
            file.name for file in self.generator_template_dir.iterdir() if file.is_dir()
        ]

        # Validate that the requested template exists
        if template not in generator_templates:
            raise ValueError(
                f"Invalid template name. Supported templates are {generator_templates}"
            )

        # Collect every file (recursively) from the generator template directory.
        generator_template_path: Path = self.generator_template_dir / template
        preprocessor_template_path: Path = self.preprocessor_template_dir / template
        generator_files = [
            file for file in generator_template_path.rglob("*") if not file.is_dir()
        ]
        preprocesor_files = [
            file for file in preprocessor_template_path.rglob("*") if not file.is_dir()
        ]
        self.files.extend(generator_files)

        # Add preprocessor files only when there is no generator file with the
        # same name — generator files take precedence.
        generator_file_names = [file.name for file in generator_files]
        for file in preprocesor_files:
            if file.name not in generator_file_names:
                self.files.append(file)

        self.jaffgen_config["template"] = template

    def __set_default_lang(self, default_lang: str | None) -> None:
        """
        Validate and store the default code-generation language.

        Parameters
        ----------
        default_lang : str or None
            Language token (e.g. ``"c"``, ``"python"``).  ``None`` is
            allowed — the template parser will infer the language from the
            file extension instead.

        Raises
        ------
        ValueError
            If *default_lang* is not recognised by
            :meth:`~jaff.codegen.Codegen.get_language_tokens`.
        """
        if default_lang and default_lang not in cg.get_language_tokens():
            raise ValueError(f"Unsupported language specified: {default_lang}")

        self.jaffgen_config["default_lang"] = default_lang

    def __set_network(self, network_file: str | None) -> None:
        """
        Resolve and validate the path to the chemical reaction network file.

        Supports both absolute paths and named built-in networks (subdirectory
        names under the ``networks/`` directory).  When a named network is
        given, the method scans the network folder for the first ``.jet`` file.

        Parameters
        ----------
        network_file : str or None
            Path to the network file, or the name of a built-in network.

        Raises
        ------
        RuntimeError
            If *network_file* is ``None``.
        FileNotFoundError
            If the resolved path does not exist, or is not a regular file.
        """
        if network_file is None:
            raise RuntimeError("No network file supplied. Please enter a network file")

        netfile = Path(network_file)
        # When the path comes from the config file (not the CLI), resolve it
        # relative to the directory that contains the config file.
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.network
        ):
            if not netfile.is_absolute():
                netfile = self.jaffgen_config["config_file_dir"] / netfile

        netfile = netfile.resolve()

        # Check whether the name matches a built-in named network directory.
        networks = {f.name for f in self.network_dir.iterdir() if f.is_dir()}
        is_predefined_network = str(netfile.name) in networks

        if not netfile.exists() and not is_predefined_network:
            raise FileNotFoundError(netfile)

        # For named networks, find the first .jet file inside that network's folder.
        if is_predefined_network:
            ndir = self.network_dir / netfile.name
            for f in ndir.iterdir():
                if f.suffix.lower() == ".jet":
                    netfile = f
                    break

        if not netfile.is_file():
            raise FileNotFoundError(f"{netfile} is not a valid file")

        self.jaffgen_config["network_file"] = netfile

    def __set_input_files(self, input_files: list[str] | None) -> None:
        """
        Validate and add explicit individual template files to the file list.

        Parameters
        ----------
        input_files : list of str or None
            Paths to individual template files (from ``--files``).
            Does nothing if ``None``.

        Raises
        ------
        FileNotFoundError
            If any listed file does not exist or is not a regular file.
        """
        if input_files is None:
            self.jaffgen_config["input_files"] = None
            return

        self.jaffgen_config["input_files"]: list[Path] = []
        for file in input_files:
            infile: Path = Path(file)
            # Resolve relative paths against the config file's directory when
            # the path comes from the config (not the CLI --files flag).
            if self.jaffgen_config["config_file_dir"] is not None and not bool(
                self.args.files
            ):
                if not infile.is_absolute():
                    infile = self.jaffgen_config["config_file_dir"] / infile

            infile = infile.resolve()

            if not infile.exists():
                raise FileNotFoundError(file)

            if not infile.is_file():
                raise FileNotFoundError(f"{file} is not a file")

            self.files.append(infile)
            self.jaffgen_config["input_files"].append(infile)

    def __set_input_dir(self, input_dir: str | None) -> None:
        """
        Add all files from a template directory to the file list.

        Parameters
        ----------
        input_dir : str or None
            Path to a directory of template files (from ``--indir``).
            Does nothing if ``None``.

        Returns
        -------
        None
        """
        if input_dir is None:
            self.jaffgen_config["input_dir"] = None
            return

        indir: Path = Path(input_dir)
        # Resolve relative paths against the config file directory when the
        # value originates from the config file rather than the CLI.
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.indir
        ):
            if not indir.is_absolute():
                indir = self.jaffgen_config["config_file_dir"] / indir

        indir = indir.resolve()

        # Add all regular files in the directory (non-recursive).
        self.files.extend([f for f in indir.iterdir() if f.is_file()])
        self.jaffgen_config["input_dir"] = indir

    def __set_funcfile(self, funcfile: str | None) -> None:
        """
        Resolve and store the auxiliary function file path in network props.

        When *funcfile* is ``None``, the Network constructor default is used
        (which typically looks for ``<network_name>.jfunc`` in the network
        directory).

        Parameters
        ----------
        funcfile : str or None
            Path to the auxiliary function file (from ``--funcfile``).

        Returns
        -------
        None
        """
        if funcfile is None:
            # Fall back to the Network constructor's default value.
            self.jaffgen_config["netprops"]["funcfile"] = self.network_params[
                "funcfile"
            ].default
            return

        funcfile: Path = Path(funcfile)
        # Resolve relative paths against the config file directory if needed.
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.funcfile
        ):
            if not funcfile.is_absolute():
                funcfile = self.jaffgen_config["config_file_dir"] / funcfile

        funcfile = funcfile.resolve()

        self.jaffgen_config["netprops"]["funcfile"] = funcfile

    def __set_output_dir(self, output_dir: str | None) -> None:
        """
        Resolve, create if necessary, and store the output directory path.

        Falls back to ``<jaff_package>/generated/`` when *output_dir* is
        ``None``.

        Parameters
        ----------
        output_dir : str or None
            Desired output directory path (from ``--outdir``).

        Raises
        ------
        NotADirectoryError
            If the resolved path exists but is not a directory.
        """
        if output_dir is None:
            self.logger.warning("No output directory has been supplied.")
            self.logger.warning(
                f"Files will be generated at {self.jaff_dir / 'generated'}"
            )

        outdir: Path = (
            Path(output_dir)
            if output_dir is not None
            else self.jaff_dir.parent.parent / "generated"
        )
        # Resolve relative output paths against the config file directory.
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.outdir
        ):
            if not outdir.is_absolute():
                outdir = self.jaffgen_config["config_file_dir"] / outdir

        outdir = outdir.resolve()

        # Create the directory on first use if it does not yet exist.
        if not outdir.exists():
            outdir.mkdir()

        if not outdir.is_dir():
            raise NotADirectoryError(f"Output path is not a directory: {outdir}")

        self.jaffgen_config["output_dir"] = outdir

    def __get_parser(self) -> argparse.ArgumentParser:
        """
        Build and return the top-level argument parser.

        Returns
        -------
        argparse.ArgumentParser
            Configured parser for the ``jaffgen`` command.
        """
        return argparse.ArgumentParser(
            prog="jaffgen",
            description="Generate code for chemical reaction networks in multiple programming languages.",
            epilog="""
            Examples:
              # Generate from a template directory
              jaffgen --network networks/react_COthin --indir templates/ --outdir output/

              # Use a predefined template collection
              jaffgen --network networks/react_COthin --template chemistry_solver --outdir output/

              # Process specific files with Rust
              jaffgen --network networks/test.dat --files rates.txt odes.txt --lang rust --outdir output/

              # Combine template and custom files
              jaffgen --network networks/test.dat --template base --files custom.cpp --outdir output/

            Supported Languages:
              c, cxx (c++, cpp), fortran (f90), python (py), rust (rs), julia (jl), r

            For more information, visit: https://jaff-chemistry.github.io/jaff/
                    """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    def __set_parser_props(self) -> None:
        """
        Register all CLI arguments on ``self.parser``.

        Organises arguments into the top-level parser and two named groups
        (``Input sources`` and ``Code generation options``).

        Returns
        -------
        None
        """
        # ---- Core arguments ------------------------------------------------
        self.parser.add_argument(
            "--config",
            required=False,
            metavar="FILE",
            help="Path to jaff config file",
        )

        self.parser.add_argument(
            "--label",
            required=False,
            metavar="TEXT",
            help="Network will be generated by the supplied label. Defaults to network file name",
        )

        self.parser.add_argument(
            "--funcfile",
            required=False,
            metavar="FILE",
            help="Path to auxiliary function file. Checks network dir for <network_name>.jfunc by default",
        )

        self.parser.add_argument(
            "--replace-nH",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Standardizes symbols when true",
        )

        self.parser.add_argument(
            "--errors",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Stops parsing if physical errors are encountered",
        )

        self.parser.add_argument(
            "--network",
            required=False,
            metavar="FILE",
            help="Path to chemical reaction network file (required)",
        )

        # ---- Output options ------------------------------------------------
        self.parser.add_argument(
            "--outdir",
            metavar="DIR",
            help="Output directory for generated files (default: jaff/generated)",
        )

        # ---- Input source options (mutually compatible) --------------------
        input_group = self.parser.add_argument_group(
            "Input sources (can combine multiple)"
        )
        input_group.add_argument(
            "--indir",
            metavar="DIR",
            help="Directory containing template files to process",
        )
        input_group.add_argument(
            "--files",
            nargs="+",
            metavar="FILE",
            help="Individual template file(s) to process",
        )
        input_group.add_argument(
            "--template",
            metavar="NAME",
            help="Name of predefined template collection in jaff/templates/generator/",
        )

        # ---- Code generation options ---------------------------------------
        gen_group = self.parser.add_argument_group("Code generation options")
        gen_group.add_argument(
            "--lang",
            metavar="LANGUAGE",
            choices=[
                "c",
                "cxx",
                "fortran",
                "python",
                "rust",
                "julia",
            ],
            help="Default programming language for unsupported files (choices: %(choices)s)",
        )

    def __handle_radiation(self, props: dict) -> None:
        """
        Populate radiation-related network parameters from the config file.

        Reads the ``[radiation]`` section of the TOML config and sets the
        corresponding keys in ``self.jaffgen_config["netprops"]``, falling
        back to Network constructor defaults for any missing entry.

        Parameters
        ----------
        props : dict
            Parsed ``[radiation]`` section from the TOML config.

        Returns
        -------
        None
        """
        net_params = signature(Network.__init__).parameters
        bands: list = props.get("bands", net_params["rad_bands"].default)
        power: int | float = props.get(
            "power_law_index", net_params["rad_powerlaw_index"].default
        )
        energy_density: bool = props.get(
            "energy_density", net_params["rad_energy_density"].default
        )
        c: float = props.get("rsl", net_params["c"].default)

        self.jaffgen_config["netprops"]["rad_bands"] = bands
        self.jaffgen_config["netprops"]["rad_powerlaw_index"] = power
        self.jaffgen_config["netprops"]["rad_energy_density"] = energy_density
        self.jaffgen_config["netprops"]["c"] = c

    def __handle_data_tables(self, props: list) -> None:
        """
        Process ``[[table]]`` entries from the TOML config and write outputs.

        Each entry is passed to :class:`~jaff.cli.ConfigTable` for parsing.
        Depending on the target format declared in the table block, the result
        is written as either an HDF5 file or a CSV file.

        Parameters
        ----------
        props : list of dict
            List of table configuration dictionaries from the ``[[table]]``
            TOML array.

        Returns
        -------
        None
        """
        assert self.jaffgen_config["config_file"] is not None

        for table_props in props:
            ct = ConfigTable(
                table_props,
                self.jaffgen_config["config_file"],
                self.jaffgen_config["network_file"],
            )
            parsed_out = ct.parse()

            # Write HDF5 output when the target format is HDF5.
            if isinstance(parsed_out, HDF5Dict):
                HDF5().from_dict(
                    self.jaffgen_config["output_dir"] / ct.target_props["path"],
                    parsed_out,
                )

            # Write CSV output when the target format is CSV.
            if isinstance(parsed_out, pd.DataFrame):
                parsed_out.to_csv(
                    self.jaffgen_config["output_dir"] / ct.target_props["path"],
                    sep=ct.target_props["delimiter"],
                )


def main():
    """Entry point registered as the ``jaffgen`` console script."""
    JaffGen()


if __name__ == "__main__":
    main()
