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

import argparse
from inspect import signature
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from .codegen import Codegen as cg
from .config_table_parser import ConfigTable
from .core.logger import JaffLogger, jaff_progress
from .drivers.hdf5 import HDF5
from .drivers.toml import Toml
from .file_parser import Fileparser
from .jaff_types import HDF5Dict
from .network import Network, NetworkProps

if TYPE_CHECKING:
    import logging


class JaffGen:
    def __init__(self):
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

        self.outdir: Path = self.__get_output_dir(self.args.outdir)
        self.netfile: Path = self.__set_network(self.args.network)
        self.default_lang: str = self.__get_default_lang(self.args.lang)
        self.jaff_config_file: Path | None = None
        self.jaff_config_dir: Path | None = None

        self.__set_input_dir(self.args.indir)
        self.__set_input_files(self.args.files)
        self.__set_network(self.args.network)
        self.__set_template(self.args.template)

        # Ensure at least one input file was provided
        if not self.files:
            raise RuntimeError("No valid input file/folder/template have been supplied")

        self.net_kwargs: NetworkProps = {"fname": str(self.netfile)}
        self.__read_jaff_config()

        # Create a new network instance
        self.net: Network = Network(**self.net_kwargs, logger=self.logger)
        self.__process_files()

    def __process_files(self):
        # Process each template file
        for file in jaff_progress.track(self.files, description="Processing files"):
            # Initialize file parser for this template
            fparser: Fileparser = Fileparser(self.net, file, self.default_lang)

            # Parse and generate code
            lines: str = fparser.parse_file()

            # Write generated code to output file
            outfile: Path = self.outdir / file.name
            with open(outfile, "w") as f:
                f.write(lines)

            self.logger.info(f"[cyan]{file.name}[/] created at {self.outdir}")

        self.logger.info("[green]Successfully generated files[/]")
        self.logger.info(f"Generated files can be found at {self.outdir}")

    def __read_jaff_config(self) -> None:
        jaff_config_index: int | None = next(
            (i for i, f in enumerate(self.files) if f.name == "jaff.toml"), None
        )

        # Set radiation related props in radiation in present
        if jaff_config_index is not None:
            self.jaff_config_file = self.files[jaff_config_index]
            self.jaff_config_dir = self.jaff_config_file.parent
            jaff_config = Toml(self.jaff_config_file)

            rad_props = jaff_config.get_key("radiation")
            if rad_props:
                self.__handle_radiation(rad_props)

            table_props = jaff_config.get_key("table")
            if table_props:
                self.__handle_data_tables(table_props)

    def __set_template(self, template: str) -> None:
        if template is None:
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

    def __get_default_lang(self, default_lang: str) -> str:
        # Ensure default language is supported by jaff code generation
        if default_lang and default_lang not in cg.get_language_tokens():
            raise ValueError(f"Unsupported language specified: {default_lang}")

        return default_lang

    def __set_network(self, network_file: str) -> Path:
        # Validate network file is provided
        if network_file is None:
            raise RuntimeError("No network file supplied. Please enter a network file")

        # Resolve and validate network file path
        netfile = Path(network_file).resolve()
        networks = {f.name for f in self.network_dir.iterdir() if f.is_file()}
        is_predefined_network = str(netfile) in networks

        if not netfile.exists() and not is_predefined_network:
            raise FileNotFoundError(f"Unable to find network file: {netfile}")

        if is_predefined_network:
            netfile = self.network_dir / netfile.name

        if not netfile.is_file():
            raise FileNotFoundError(f"{netfile} is not a valid file")

        return netfile

    def __set_input_files(self, input_files: list[str]) -> None:
        if input_files is None:
            return

        for file in input_files:
            infile: Path = Path(file).resolve()

            if not infile.exists():
                raise FileNotFoundError(f"Invalid file path {file}")

            if not infile.is_file():
                raise FileNotFoundError(f"{file} is not a file")

            self.files.append(infile)

    def __set_input_dir(self, input_dir: str) -> None:
        if input_dir is None:
            return

        indir: Path = Path(input_dir).resolve()
        self.files.extend([f for f in indir.iterdir() if f.is_file()])

    def __get_output_dir(self, output_dir: str) -> Path:
        if output_dir is None:
            self.logger.warning("No output directory has been supplied.")
            self.logger.warning(f"Files will be generated at {Path.cwd()}")

        outdir: Path = (
            Path(output_dir).resolve()
            if output_dir is not None
            else self.jaff_dir / "generated"
        )

        # Create output directory if it doesn't exist
        if not outdir.exists():
            Path.mkdir(outdir)

        if not outdir.is_dir():
            raise NotADirectoryError(f"Output path is not a directory: {outdir}")

        return outdir

    def __get_parser(self) -> argparse.ArgumentParser:
        return argparse.ArgumentParser(
            prog="jaff.generate",
            description="Generate code for chemical reaction networks in multiple programming languages.",
            epilog="""
            Examples:
              # Generate from a template directory
              python -m jaff.generate --network networks/react_COthin --indir templates/ --outdir output/

              # Use a predefined template collection
              python -m jaff.generate --network networks/react_COthin --template chemistry_solver --outdir output/

              # Process specific files with Rust
              python -m jaff.generate --network networks/test.dat --files rates.txt odes.txt --lang rust --outdir output/

              # Combine template and custom files
              python -m jaff.generate --network networks/test.dat --template base --files custom.cpp --outdir output/

            Supported Languages:
              c, cxx (c++, cpp), fortran (f90), python (py), rust (rs), julia (jl), r

            For more information, visit: https://github.com/tgrassi/jaff
                    """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    def __set_parser_props(self):
        # Required arguments
        self.parser.add_argument(
            "--network",
            required=True,
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

        self.net_kwargs["rad_bands"] = bands
        self.net_kwargs["rad_powerlaw_index"] = power
        self.net_kwargs["rad_energy_density"] = energy_density
        self.net_kwargs["c"] = c

    def __handle_data_tables(self, props: list):
        assert self.jaff_config_dir is not None
        assert self.jaff_config_file is not None

        for table_props in props:
            ct = ConfigTable(table_props, self.jaff_config_file, self.netfile)
            parsed_out = ct.parse()

            if isinstance(parsed_out, HDF5Dict):
                HDF5().from_dict(self.outdir / ct.target_props["path"], parsed_out)

            if isinstance(parsed_out, pd.DataFrame):
                parsed_out.to_csv(
                    self.outdir / ct.target_props["path"],
                    sep=ct.target_props["delimiter"],
                )


def main():
    JaffGen()


if __name__ == "__main__":
    main()
