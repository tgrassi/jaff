"""
JAFF Code Generator CLI Interface.

This module provides the command-line interface for the JAFF (Just Another File Format)
code generator. It processes template files containing JAFF directives and generates
code for chemical reaction networks in various programming languages (C, C++, Fortran,
Python, Rust, Julia, R).

Usage:
    python -m jaff.generate --network <network_file> [--outdir <dir>] [--indir <dir>] [--files <file1> <file2> ...]

Examples:
    # Generate code from a specific template directory
    python -m jaff.generate --network networks/react_COthin --indir templates/ --outdir output/

    # Use a predefined template collection
    python -m jaff.generate --network networks/react_COthin --template my_template --outdir output/

    # Process specific files with a default language
    python -m jaff.generate --network networks/test.dat --files file1.txt file2.txt --lang rust
"""

from __future__ import annotations

import argparse
from inspect import signature
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

import pandas as pd

from .codegen import Codegen as cg
from .common.welcome import motd
from .config_table_parser import ConfigTable
from .core.logger import JaffLogger, jaff_progress
from .drivers.hdf5 import HDF5
from .drivers.toml import Toml
from .file_parser import Fileparser
from .jaff_types import HDF5Dict
from .network import Network

if TYPE_CHECKING:
    import logging

    from sympy import Basic

NETWORK_PROPS = TypedDict(
    "NETWORK_PROPS",
    {
        "fname": Path,
        "label": str | None,
        "funcfile": Path | None,
        "replace_nH": bool,
        "errors": bool,
        "rad_bands": list[str | int | float | "Basic"],
        "rad_powerlaw_index": int | float,
        "rad_energy_density": bool,
        "c": float,
        "_from_cli": bool,
    },
)

JAFFGEN_PROPS = TypedDict(
    "JAFFGEN_PROPS",
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
        "netprops": NETWORK_PROPS,
    },
)


class JaffGen:
    def __init__(self):
        print(motd("jaffgen"))
        self.parser: argparse.ArgumentParser = self.__get_parser()
        self.__set_parser_props()

        self.logger: logging.Logger = JaffLogger().get_logger()
        self.args: argparse.Namespace = self.parser.parse_args()

        # Locate JAFF package directory and built-in template directory
        # Templates are stored in jaff/templates/generator/
        self.jaff_dir: Path = Path(__file__).parent
        self.network_dir: Path = self.jaff_dir.parent.parent / "networks"
        self.generator_template_dir: Path = self.jaff_dir / "templates" / "generator"
        self.preprocessor_template_dir: Path = (
            self.jaff_dir / "templates" / "preprocessor"
        )
        self.files: list[Path] = []
        self.jaffgen_config: JAFFGEN_PROPS = {"netprops": {}}  # type: ignore
        self.jaffgen_config_raw: Toml | None = None

        self.jaffgen_config["config_file"] = None
        self.jaffgen_config["config_file_dir"] = None

        # Overrides config present in directories or files list
        self.__set_config(self.args.config)
        self.__set_input_dir(self.args.indir)
        self.__set_input_files(self.args.files)
        self.__set_template(self.args.template)

        self.__read_jaff_config_from_files()

        if not self.args.indir:
            self.__set_input_dir(self.__get_prop(None, "jaffgen", "input_dir"))
        if not self.args.files:
            self.__set_input_files(self.__get_prop(None, "jaffgen", "input_files"))
        if not self.args.template:
            self.__set_template(self.__get_prop(None, "jaffgen", "template"))

        # Ensure at least one input file was provided
        if not self.files:
            raise RuntimeError("No valid input file/folder/template have been supplied")

        self.__set_network(self.__get_prop(self.args.network, "jaffgen", "network"))
        self.__set_output_dir(self.__get_prop(self.args.outdir, "jaffgen", "output_dir"))
        self.__set_default_lang(
            self.__get_prop(self.args.lang, "jaffgen", "default_lang")
        )

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

        if self.jaffgen_config_raw:
            rad_props = self.jaffgen_config_raw.get_key("radiation")
            if rad_props:
                self.__handle_radiation(rad_props)

            table_props = self.jaffgen_config_raw.get_key("table")
            if table_props:
                self.__handle_data_tables(table_props)

        # Create a new network instance
        self.net: Network = Network(**self.jaffgen_config["netprops"])
        self.__process_files()

    def __get_prop(
        self, arg_prop: str | None, dict_key: str, dict_prop: str
    ) -> Any | None:
        return arg_prop or (
            (self.jaffgen_config_raw.get_key(dict_key) or {}).get(dict_prop, None)
            if self.jaffgen_config_raw is not None
            else None
        )

    def __set_config(self, config_file: str | Path | None) -> None:
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
        self.jaffgen_config_raw = Toml(config_file)

    def __process_files(self):
        # Process each template file
        for file in jaff_progress.track(self.files, description="Processing files"):
            # Initialize file parser for this template
            fparser: Fileparser = Fileparser(
                self.net, file, self.jaffgen_config["default_lang"]
            )

            # Parse and generate code
            lines: str = fparser.parse_file()

            # Write generated code to output file
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
        if self.jaffgen_config["config_file"] is not None:
            return

        jaff_config_index: int | None = next(
            (i for i, f in enumerate(self.files) if f.name == "jaff.toml"), None
        )

        if jaff_config_index is not None:
            self.__set_config(self.files[jaff_config_index])

    def __set_template(self, template: str | None) -> None:
        if template is None:
            self.jaffgen_config["template"] = None
            return

        # Handle predefined template directory if specified
        # Get list of available template directory names
        # Each subdirectory in templates/generator/ is a template collection
        generator_templates: list[str] = [
            file.name for file in self.generator_template_dir.iterdir() if file.is_dir()
        ]

        # Validate that the requested template exists
        if template not in generator_templates:
            raise ValueError(
                f"Invalid template name. Supported templates are {generator_templates}"
            )

        # Recursively collect all files from the template directory
        generator_template_path: Path = self.generator_template_dir / template
        preprocessor_template_path: Path = self.preprocessor_template_dir / template
        generator_files = [
            file for file in generator_template_path.rglob("*") if not file.is_dir()
        ]
        preprocesor_files = [
            file for file in preprocessor_template_path.rglob("*") if not file.is_dir()
        ]
        self.files.extend(generator_files)

        # Keep preproc files that don't have a corresponding generator file, otherwise use the generator file
        generator_file_names = [file.name for file in generator_files]
        for file in preprocesor_files:
            if file.name not in generator_file_names:
                self.files.append(file)

        self.jaffgen_config["template"] = template

    def __set_default_lang(self, default_lang: str | None) -> None:
        # Ensure default language is supported by jaff code generation
        if default_lang and default_lang not in cg.get_language_tokens():
            raise ValueError(f"Unsupported language specified: {default_lang}")

        self.jaffgen_config["default_lang"] = default_lang

    def __set_network(self, network_file: str | None) -> None:
        # Validate network file is provided
        if network_file is None:
            raise RuntimeError("No network file supplied. Please enter a network file")

        # Resolve and validate network file path
        netfile = Path(network_file)
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.network
        ):
            if not netfile.is_absolute():
                netfile = self.jaffgen_config["config_file_dir"] / netfile

        netfile = netfile.resolve()

        networks = {f.name for f in self.network_dir.iterdir() if f.is_dir()}
        is_predefined_network = str(netfile.name) in networks

        if not netfile.exists() and not is_predefined_network:
            raise FileNotFoundError(netfile)

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
        if input_files is None:
            self.jaffgen_config["input_files"] = None
            return

        self.jaffgen_config["input_files"]: list[Path] = []
        for file in input_files:
            infile: Path = Path(file)
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
        if input_dir is None:
            self.jaffgen_config["input_dir"] = None
            return

        indir: Path = Path(input_dir)
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.indir
        ):
            if not indir.is_absolute():
                indir = self.jaffgen_config["config_file_dir"] / indir

        indir = indir.resolve()

        self.files.extend([f for f in indir.iterdir() if f.is_file()])
        self.jaffgen_config["input_dir"] = indir

    def __set_funcfile(self, funcfile: str | None) -> None:
        if funcfile is None:
            self.jaffgen_config["netprops"]["funcfile"] = self.network_params[
                "funcfile"
            ].default
            return

        funcfile: Path = Path(funcfile)
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.funcfile
        ):
            if not funcfile.is_absolute():
                funcfile = self.jaffgen_config["config_file_dir"] / funcfile

        funcfile = funcfile.resolve()

        self.jaffgen_config["netprops"]["funcfile"] = funcfile

    def __set_output_dir(self, output_dir: str | None) -> None:
        if output_dir is None:
            self.logger.warning("No output directory has been supplied.")
            self.logger.warning(
                f"Files will be generated at {self.jaff_dir / 'generated'}"
            )

        outdir: Path = (
            Path(output_dir) if output_dir is not None else self.jaff_dir / "generated"
        )
        if self.jaffgen_config["config_file_dir"] is not None and not bool(
            self.args.outdir
        ):
            if not outdir.is_absolute():
                outdir = self.jaffgen_config["config_file_dir"] / outdir

        outdir = outdir.resolve()

        # Create output directory if it doesn't exist
        if not outdir.exists():
            outdir.mkdir()

        if not outdir.is_dir():
            raise NotADirectoryError(f"Output path is not a directory: {outdir}")

        self.jaffgen_config["output_dir"] = outdir

    def __get_parser(self) -> argparse.ArgumentParser:
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

    def __set_parser_props(self):
        # Required arguments
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

        # Output options
        self.parser.add_argument(
            "--outdir",
            metavar="DIR",
            help="Output directory for generated files (default: jaff/generated)",
        )

        # Input source options (mutually compatible)
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

        # Code generation options
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

    def __handle_data_tables(self, props: list):
        assert self.jaffgen_config["config_file"] is not None

        for table_props in props:
            ct = ConfigTable(
                table_props,
                self.jaffgen_config["config_file"],
                self.jaffgen_config["network_file"],
            )
            parsed_out = ct.parse()

            if isinstance(parsed_out, HDF5Dict):
                HDF5().from_dict(
                    self.jaffgen_config["output_dir"] / ct.target_props["path"],
                    parsed_out,
                )

            if isinstance(parsed_out, pd.DataFrame):
                parsed_out.to_csv(
                    self.jaffgen_config["output_dir"] / ct.target_props["path"],
                    sep=ct.target_props["delimiter"],
                )


def main():
    JaffGen()


if __name__ == "__main__":
    main()
