"""
JAFF Quick-analysis CLI Interface.

This module provides the ``jaffx`` command-line entry point for rapid
inspection and export of chemical reaction networks without running the full
code-generation pipeline.

Sub-commands
------------
export hdf5
    Export rate coefficients as a function of temperature to an HDF5 file.
export txt
    Export rate coefficients to a plain-text (whitespace-separated) file.
export jaff
    Export the network to a gzip-compressed JSON ``.jaff`` file.
get num-species
    Print the total number of species in the network.
get num-reactions
    Print the total number of reactions in the network.

Usage
-----
::

    jaffx <command> <format> --network <file> [options]

Examples
--------
::

    jaffx export hdf5 --network my_net.jet --file output.h5
    jaffx export txt  --network my_net.jet --tmin 10 --tmax 1e4 --nT 200
    jaffx get num-species --network my_net.jet
"""

import argparse
import logging
from inspect import signature

from .. import Network, NetworkProps
from ..common import motd
from ..io import JaffLogger


class JaffX:
    """
    Entry-point class for the ``jaffx`` CLI command.

    Instantiating this class drives the full interaction lifecycle:

    1. Print the JAFF message-of-the-day banner.
    2. Build the argument parser with all sub-commands.
    3. Parse ``sys.argv`` and dispatch to the appropriate action handler.

    Parameters
    ----------
    None
        Arguments are read directly from ``sys.argv`` via :mod:`argparse`.
    """

    def __init__(self):
        """Drive the full ``jaffx`` interaction lifecycle from CLI arguments.

        Prints the MOTD banner, builds the argument parser, parses ``sys.argv``,
        and dispatches to the appropriate action handler (``export`` or ``get``
        sub-command).
        """
        print(motd("jaffx"))
        self.logger: logging.Logger = JaffLogger().get_logger()
        self.parser: argparse.ArgumentParser = self.__get_parser()
        # Register the two top-level sub-command groups (export, get).
        self.subparsers = self.parser.add_subparsers(dest="command", required=True)
        self.__set_subparsers()

        self.args: argparse.Namespace = self.parser.parse_args()
        # Dispatch to whichever handler was wired up by set_defaults(func=...).
        self.args.func(self.args)

    # ------------------------------------------------------------------
    # Parser construction
    # ------------------------------------------------------------------

    def __get_parser(self) -> argparse.ArgumentParser:
        """
        Build and return the top-level ``jaffx`` argument parser.

        Returns
        -------
        argparse.ArgumentParser
            Configured root parser for the ``jaffx`` command.
        """
        return argparse.ArgumentParser(
            prog="jaffx",
            description="CLI tool for quick network parsing and analysis",
            epilog="""
            Examples:
                Will be updated

            For more information, visit: https://jaff-chemistry.github.io/jaff/
                    """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    def __set_subparsers(self) -> None:
        """
        Register all top-level sub-command parsers.

        Currently wires up ``export`` and ``get`` sub-command groups.

        Returns
        -------
        None
        """
        parser_funcs = [self.__set_export_comm, self.__set_get_comm]
        for parser_func in parser_funcs:
            parser_func()

    # ------------------------------------------------------------------
    # "export" sub-command
    # ------------------------------------------------------------------

    def __set_export_comm(self) -> None:
        """
        Register the ``export`` sub-command group.

        Creates the ``export`` parser and attaches format-specific
        sub-parsers: ``hdf5``, ``txt``, and ``jaff``.

        Returns
        -------
        None
        """
        export_parser = self.subparsers.add_parser(
            "export",
            help="Exports the network file in specified format",
        )
        esp = export_parser.add_subparsers(dest="format", required=True)
        self.__set_export_hdf5(esp)
        self.__set_export_txt(esp)
        self.__set_export_jaff(esp)

    def __set_export_txt(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        """
        Register the ``export txt`` sub-parser.

        Adds all arguments needed to export rate coefficients to a
        whitespace-separated text file, including tabulation range,
        adaptive-sampling controls, and clipping options.

        Parameters
        ----------
        esp : argparse._SubParsersAction
            The parent sub-parsers action to attach this parser to.

        Returns
        -------
        None
        """
        parser = esp.add_parser(
            "txt",
            help="Exports reaction rate coefficients for all reactions as a function of temperature to text format",
        )
        parser.set_defaults(func=self.__export_to_txt)
        self.__set_network_args(parser)

        txt_grp = parser.add_argument_group("Txt file processing properties")

        txt_grp.add_argument(
            "-f",
            "--file",
            metavar="FILE",
            help="Output file path/name",
        )

        txt_grp.add_argument(
            "--tmin",
            metavar="VALUE",
            help="Minimum temperature for the tabulation. Minimum temperature over reactions if unspecified",
        )

        txt_grp.add_argument(
            "--tmax",
            metavar="VALUE",
            help="Maximum temperature for the tabulation. Maximum temperature over reactions if unspecified",
        )

        txt_grp.add_argument(
            "--nT",
            metavar="INT",
            help="Initial guess for the number of sampling temperatures",
        )

        txt_grp.add_argument(
            "--err-tol",
            metavar="FLOAT",
            help="Relative error tolerance for interpolation. Adaptive sampling is disabled and the table size will be exactly nT if unspecified",
        )

        txt_grp.add_argument(
            "--rate-min",
            metavar="FLOAT",
            help="Adaptive error toleracne is not applied to rates below minimum rate",
        )

        txt_grp.add_argument(
            "--rate-max",
            metavar="FLOAT",
            help="Rates above max rate is clipped to prevent overflow",
        )

        txt_grp.add_argument(
            "--fast-log",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Sample points are equally spaced in fast_log2(T) rather than log(T)",
        )

        txt_grp.add_argument(
            "--include-all",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Include all reactions, setting non-tabulatable rates to NaN. Otherwise, only include tabulatable, non-constant coefficients.",
        )

        txt_grp.add_argument(
            "-v",
            "--verbose",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Produces verbose output while adaptively refining",
        )

    def __set_export_hdf5(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        """
        Register the ``export hdf5`` sub-parser.

        Adds all arguments needed to export rate coefficients to an HDF5
        file, mirroring the options available for text export.

        Parameters
        ----------
        esp : argparse._SubParsersAction
            The parent sub-parsers action to attach this parser to.

        Returns
        -------
        None
        """
        parser = esp.add_parser(
            "hdf5",
            help="Exports reaction rate coefficients for all reactions as a function of temperature to hdf5 format",
        )
        parser.set_defaults(func=self.__export_to_hdf5)
        self.__set_network_args(parser)

        hdf5_grp = parser.add_argument_group("HDF5 file processing properties")

        hdf5_grp.add_argument(
            "-f",
            "--file",
            metavar="FILE",
            help="Output file path/name",
        )

        hdf5_grp.add_argument(
            "--tmin",
            metavar="VALUE",
            help="Minimum temperature for the tabulation. Minimum temperature over reactions if unspecified",
        )

        hdf5_grp.add_argument(
            "--tmax",
            metavar="VALUE",
            help="Maximum temperature for the tabulation. Maximum temperature over reactions if unspecified",
        )

        hdf5_grp.add_argument(
            "--nT",
            metavar="INT",
            help="Initial guess for the number of sampling temperatures",
        )

        hdf5_grp.add_argument(
            "--err-tol",
            metavar="FLOAT",
            help="Relative error tolerance for interpolation. Adaptive sampling is disabled and the table size will be exactly nT if unspecified",
        )

        hdf5_grp.add_argument(
            "--rate-min",
            metavar="FLOAT",
            help="Adaptive error toleracne is not applied to rates below minimum rate",
        )

        hdf5_grp.add_argument(
            "--rate-max",
            metavar="FLOAT",
            help="Rates above max rate is clipped to prevent overflow",
        )

        hdf5_grp.add_argument(
            "--fast-log",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Sample points are equally spaced in fast_log2(T) rather than log(T)",
        )

        hdf5_grp.add_argument(
            "--include-all",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Include all reactions, setting non-tabulatable rates to NaN. Otherwise, only include tabulatable, non-constant coefficients.",
        )

        hdf5_grp.add_argument(
            "-v",
            "--verbose",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Produces verbose output while adaptively refining",
        )

    def __set_export_jaff(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        """
        Register the ``export jaff`` sub-parser.

        Adds arguments for exporting the entire network to a
        gzip-compressed JSON ``.jaff`` file.

        Parameters
        ----------
        esp : argparse._SubParsersAction
            The parent sub-parsers action to attach this parser to.

        Returns
        -------
        None
        """
        parser = esp.add_parser(
            "jaff",
            help="Exports the network to a .jaff file (gzip-compressed JSON payload)",
        )
        parser.set_defaults(func=self.__export_to_jaff)
        self.__set_network_args(parser)

        jaff_grp = parser.add_argument_group("JAFF file processing properties")

        jaff_grp.add_argument(
            "-f",
            "--file",
            metavar="FILE",
            help="Output file path/name",
        )

    def __set_network_args(self, parser: argparse.ArgumentParser) -> None:
        """
        Add the shared network-property argument group to *parser*.

        These arguments are common to every sub-command that needs to load a
        :class:`~jaff.Network` (``export`` and ``get`` sub-commands).

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The sub-command parser to augment.

        Returns
        -------
        None
        """
        network_grp = parser.add_argument_group("Network properties")
        network_grp.add_argument(
            "--network",
            metavar="FILE",
            help="Path ot chemical reaction network file (required)",
        )

        network_grp.add_argument(
            "--label",
            metavar="NAME",
            help="Network label",
        )

        network_grp.add_argument(
            "--funcfile",
            metavar="FILE",
            help="Path to auxiliary function file. Scans network directory by default",
        )

        network_grp.add_argument(
            "--replace-nh",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Standardize hydrogen density symbols if true",
        )

    # ------------------------------------------------------------------
    # "get" sub-command
    # ------------------------------------------------------------------

    def __set_get_comm(self) -> None:
        """
        Register the ``get`` sub-command group.

        Creates the ``get`` parser and attaches ``num-species`` and
        ``num-reactions`` sub-parsers.

        Returns
        -------
        None
        """
        export_parser = self.subparsers.add_parser(
            "get",
            help="Get network properties",
        )
        esp = export_parser.add_subparsers(dest="format", required=True)
        self.__set_get_nspec(esp)
        self.__set_get_nreact(esp)

    def __set_get_nspec(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        """
        Register the ``get num-species`` sub-parser.

        Parameters
        ----------
        esp : argparse._SubParsersAction
            The parent sub-parsers action to attach this parser to.

        Returns
        -------
        None
        """
        parser = esp.add_parser("num-species", help="Prints the number of species")
        parser.set_defaults(func=self.__get_nspec)
        self.__set_network_args(parser)

    def __set_get_nreact(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        """
        Register the ``get num-reactions`` sub-parser.

        Parameters
        ----------
        esp : argparse._SubParsersAction
            The parent sub-parsers action to attach this parser to.

        Returns
        -------
        None
        """
        parser = esp.add_parser("num-reactions", help="Prints the number of reactions")
        parser.set_defaults(func=self.__get_nreact)
        self.__set_network_args(parser)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def __export_to_txt(self, args) -> None:
        """
        Handle ``jaffx export txt``.

        Loads the network and calls :meth:`~jaff.Network.to_txt`, forwarding
        all tabulation and sampling arguments.  Any argument left at its CLI
        default (``None``) is replaced by the corresponding
        :meth:`~jaff.Network.to_txt` parameter default.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed command-line arguments for this sub-command.

        Returns
        -------
        None
        """
        mparams = signature(Network.to_txt).parameters
        net = self.__get_network(args)
        kwargs = {
            "fname": args.file,
            "T_min": args.tmin or mparams["T_min"].default,
            "T_max": args.tmax or mparams["T_max"].default,
            "nT": args.nT or mparams["nT"].default,
            "err_tol": args.err_tol or mparams["err_tol"].default,
            "rate_min": args.rate_min or mparams["rate_min"].default,
            "rate_max": args.rate_max or mparams["rate_max"].default,
            # Boolean options need an explicit None-check to distinguish
            # "not supplied" from a deliberate False.
            "fast_log": args.fast_log
            if args.fast_log is not None
            else mparams["fast_log"].default,
            "include_all": args.include_all
            if args.include_all is not None
            else mparams["include_all"].default,
            "verbose": args.verbose
            if args.verbose is not None
            else mparams["verbose"].default,
        }

        net.to_txt(**kwargs)

    def __export_to_hdf5(self, args) -> None:
        """
        Handle ``jaffx export hdf5``.

        Loads the network and calls :meth:`~jaff.Network.to_hdf5`, forwarding
        all tabulation and sampling arguments.  Any argument left at its CLI
        default (``None``) is replaced by the corresponding
        :meth:`~jaff.Network.to_hdf5` parameter default.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed command-line arguments for this sub-command.

        Returns
        -------
        None
        """
        mparams = signature(Network.to_hdf5).parameters
        net = self.__get_network(args)
        kwargs = {
            "fname": args.file,
            "T_min": args.tmin or mparams["T_min"].default,
            "T_max": args.tmax or mparams["T_max"].default,
            "nT": args.nT or mparams["nT"].default,
            "err_tol": args.err_tol or mparams["err_tol"].default,
            "rate_min": args.rate_min or mparams["rate_min"].default,
            "rate_max": args.rate_max or mparams["rate_max"].default,
            "fast_log": args.fast_log
            if args.fast_log is not None
            else mparams["fast_log"].default,
            "include_all": args.include_all
            if args.include_all is not None
            else mparams["include_all"].default,
            "verbose": args.verbose
            if args.verbose is not None
            else mparams["verbose"].default,
        }

        net.to_hdf5(**kwargs)

    def __export_to_jaff(self, args) -> None:
        """
        Handle ``jaffx export jaff``.

        Exports the network to a ``.jaff`` (gzip-compressed JSON) file via
        :meth:`~jaff.Network.to_hdf5`.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed command-line arguments for this sub-command.

        Returns
        -------
        None
        """
        net = self.__get_network(args)
        kwargs = {"filename": args.file}

        net.to_hdf5(**kwargs)

    def __get_nspec(self, args) -> None:
        """
        Handle ``jaffx get num-species``.

        Loads the network and logs the total species count.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed command-line arguments for this sub-command.

        Returns
        -------
        None
        """
        net = self.__get_network(args)
        self.logger.info(f"Total number of species: {net.species.count}")

    def __get_nreact(self, args) -> None:
        """
        Handle ``jaffx get num-reactions``.

        Loads the network and logs the total reaction count.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed command-line arguments for this sub-command.

        Returns
        -------
        None
        """
        net = self.__get_network(args)
        self.logger.info(f"Total number of reactions: {net.reactions.count}")

    def __get_network(self, args) -> Network:
        """
        Construct and return a :class:`~jaff.Network` from parsed CLI args.

        Fills in any missing arguments with the corresponding
        :class:`~jaff.Network` constructor defaults, then builds the
        :data:`~jaff.NetworkProps` typed dict and instantiates the network.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed command-line arguments that include network-property fields
            (``network``, ``funcfile``, ``label``, ``replace_nh``).

        Returns
        -------
        Network
            Parsed and validated chemical reaction network.
        """
        net_params = signature(Network.__init__).parameters
        net_kwargs: NetworkProps = {
            "fname": args.network,
            "funcfile": args.funcfile or net_params["funcfile"].default,
            "label": args.label or net_params["label"].default,
            # Use an explicit None check for the boolean flag so that --no-replace-nh
            # (which yields False) is not silently ignored.
            "replace_nH": args.replace_nh
            if args.replace_nh is not None
            else net_params["replace_nH"].default,
            "_from_cli": True,
        }

        return Network(**net_kwargs)


def main():
    """Entry point registered as the ``jaffx`` console script."""
    JaffX()


if __name__ == "__main__":
    main()
