import argparse
import logging
from inspect import signature

from jaff.network import NetworkProps

from .. import Network
from ..common.welcome import motd
from ..core.logger import JaffLogger


class JaffX:
    def __init__(self):
        print(motd("jaffx"))
        self.logger: logging.Logger = JaffLogger().get_logger()
        self.parser: argparse.ArgumentParser = self.__get_parser()
        self.subparsers = self.parser.add_subparsers(dest="command", required=True)
        self.__set_subparsers()

        self.args: argparse.Namespace = self.parser.parse_args()
        self.args.func(self.args)

    def __get_parser(self) -> argparse.ArgumentParser:
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
        parser_funcs = [self.__set_export_comm, self.__set_get_comm]
        for parser_func in parser_funcs:
            parser_func()

    def __set_export_comm(self) -> None:
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
            metavar="BOOL",
            help="If enabled, sample points are equally spaced in fast_log2(T) rather than log(T)",
        )

        txt_grp.add_argument(
            "--include-all",
            metavar="BOOL",
            help="Include all reactions, setting non-tabulatable rates to NaN. Otherwise, only include tabulatable, non-constant coefficients.",
        )

        txt_grp.add_argument(
            "-v",
            "--verbose",
            metavar="BOOL",
            help="If enabled, produces verbose output while adaptively refining",
        )

    def __set_export_hdf5(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
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
            metavar="BOOL",
            help="If enabled, sample points are equally spaced in fast_log2(T) rather than log(T)",
        )

        hdf5_grp.add_argument(
            "--include-all",
            metavar="BOOL",
            help="Include all reactions, setting non-tabulatable rates to NaN. Otherwise, only include tabulatable, non-constant coefficients.",
        )

        hdf5_grp.add_argument(
            "-v",
            "--verbose",
            metavar="BOOL",
            help="If enabled, produces verbose output while adaptively refining",
        )

    def __set_export_jaff(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
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
            metavar="BOOL",
            help="Standardize hydrogen density symbols if true",
        )

    def __set_get_comm(self) -> None:
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
        parser = esp.add_parser("num-species", help="Prints the number of species")
        parser.set_defaults(func=self.__get_nspec)
        self.__set_network_args(parser)

    def __set_get_nreact(
        self, esp: "argparse._SubParsersAction[argparse.ArgumentParser]"
    ) -> None:
        parser = esp.add_parser("num-reactions", help="Prints the number of species")
        parser.set_defaults(func=self.__get_nreact)
        self.__set_network_args(parser)

    def __export_to_txt(self, args) -> None:
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
            "fast_log": args.fast_log or mparams["fast_log"].default,
            "include_all": args.include_all or mparams["include_all"].default,
            "verbose": args.verbose or mparams["verbose"].default,
        }

        net.to_txt(**kwargs)

    def __export_to_hdf5(self, args) -> None:
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
            "fast_log": args.fast_log or mparams["fast_log"].default,
            "include_all": args.include_all or mparams["include_all"].default,
            "verbose": args.verbose or mparams["verbose"].default,
        }

        net.to_hdf5(**kwargs)

    def __export_to_jaff(self, args) -> None:
        net = self.__get_network(args)
        kwargs = {"filename": args.file}

        net.to_hdf5(**kwargs)

    def __get_nspec(self, args) -> None:
        net = self.__get_network(args)
        self.logger.info(f"Total number of species: {net.species.count}")

    def __get_nreact(self, args) -> None:
        net = self.__get_network(args)
        self.logger.info(f"Total number of reactions: {net.reactions.count}")

    def __get_network(self, args) -> Network:
        net_params = signature(Network.__init__).parameters
        net_kwargs: NetworkProps = {
            "fname": args.network,
            "funcfile": args.funcfile or net_params["funcfile"].default,
            "label": args.label or net_params["label"].default,
            "replace_nH": args.replace_nh or net_params["replace_nH"].default,
            "_from_cli": True,
        }

        return Network(**net_kwargs)


def main():
    JaffX()


if __name__ == "__main__":
    main()
