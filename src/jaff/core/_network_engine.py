import logging
import re
from pathlib import Path
from typing import Callable, TypedDict

from sympy import Basic, parse_expr

from ..common import f90_convert, resolve_symbolic_dependencies
from ..errors import ParserError
from ..io import JaffLogger, jaff_progress

patternProps = TypedDict(
    "patternProps",
    {
        "global_re": re.Pattern,
        "local_re": re.Pattern,
        "handler": Callable[..., None],
    },
)

uncompiledPatternProps = TypedDict(
    "uncompiledPatternProps",
    {
        "global_re": str,
        "local_re": str,
        "handler": Callable[..., None],
    },
)

kromeFormatProps = TypedDict(
    "kromeFormatProps",
    {
        "format_nline": int,
        "idx": bool,
        "nreact": int,
        "nprod": int,
        "tmin": bool,
        "tmax": bool,
        "rate": bool,
    },
)

prizmoFormatProps = TypedDict(
    "prizmoFormatProps",
    {
        "parse_vars": bool,
    },
)

networkFormatProps = TypedDict(
    "networkFormatProps",
    {
        "prizmo": prizmoFormatProps,
        "krome": kromeFormatProps,
    },
)

parsedListProps = TypedDict(
    "parsedListProps",
    {
        "r": list[str],
        "p": list[str],
        "tmin": float | None,
        "tmax": float | None,
        "rate": str,
        "string": str,
    },
)


class NetworkParser:
    def __init__(self, file: str | Path, logger: logging.Logger | None = None):
        if isinstance(file, str):
            file = Path(file)
        if not isinstance(file, (str, Path)):
            raise ValueError(f"Invalid file type detected for {file}: {type(file)}")

        file = file.resolve()
        if not file.exists():
            raise FileNotFoundError(file)

        self.__file: Path = file
        self.__logger: logging.Logger = logger or JaffLogger().get_logger()
        self.__line: str = ""
        self.__nline: int = 0
        self.__globals: dict[str, Basic] = {}  # Stores global custom variables
        self.__matched_group: None | re.Match = None
        self.__local_pattern: None | re.Pattern = None
        self.__matched_handler: None | Callable[..., None] = None
        self.__set_known_replacments()

        self.__format_props: networkFormatProps = {
            "prizmo": {"parse_vars": False},
            "krome": {
                "format_nline": 0,
                "idx": True,
                "nreact": 3,
                "nprod": 4,
                "tmin": True,
                "tmax": True,
                "rate": True,
            },
        }
        self.__valid_patterns = self.__global_patterns_dict()
        self.__parsed_list: list[parsedListProps] = []

        self.__parse_file()
        self.__normalize_rates()
        self.__globals = resolve_symbolic_dependencies(self.__globals, fname=self.__file)

    def __enter__(self) -> "NetworkParser":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__valid_patterns.clear()

        return

    def get_parsed(self) -> tuple[list[parsedListProps], dict[str, Basic]]:
        return self.__parsed_list, resolve_symbolic_dependencies(
            dep_map=self.__globals, fname=self.__file
        )

    def __parse_file(self) -> None:
        with open(self.__file, "r") as f:
            lines = f.readlines()
            for i, line in enumerate(
                jaff_progress.track(lines, description=f"Parsing {self.__file.name}")
            ):
                self.__nline = i + 1
                self.__line = line
                self.__parse_line()

    def __parse_line(self) -> None:
        if not self.__line.strip():
            return
        for _, pattern_dict in self.__valid_patterns.items():
            if match := pattern_dict["global_re"].match(self.__line):
                self.__matched_group = match
                self.__local_pattern = pattern_dict["local_re"]
                self.__matched_handler = pattern_dict["handler"]
                break

        if self.__matched_handler is not None:
            self.__matched_handler()
            self.__matched_group = None
            self.__local_pattern = None
            self.__matched_handler = None

    def __raise_error(self, message: str, **kwargs) -> None:
        raise ParserError(message, self.__line, self.__nline, self.__file, **kwargs)

    def __handle_krome_format(self) -> None:
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__handle_krome_format_errors()

        self.__format_props["krome"] = {
            "format_nline": self.__nline,
            "idx": bool(match.group("idx")),
            "nreact": match.group("reactants").lower().count("r"),
            "nprod": match.group("products").lower().count("p"),
            "tmin": bool(match.group("tmin")),
            "tmax": bool(match.group("tmax")),
            "rate": bool(match.group("rate")),
        }

        self.__valid_patterns = self.__global_patterns_dict()

    def __handle_krome_format_errors(self):
        assert self.__matched_group is not None
        format = self.__matched_group.group("format")
        if format is None:
            self.__raise_error("Empty @format KROME declerative")

        format = format.strip()
        if not format:
            self.__raise_error("Empty @format KROME declerative")

        if "," not in format:
            self.__raise_error(
                "Invalid @format KROME declerative\n"
                "@format decelerative must be separated by ','"
            )

        expected_tokens = {"idx", "R", "P", "tmin", "tmax", "rate"}
        tokens = [token.strip() for token in format.split(",")]
        for token in tokens:
            if token not in expected_tokens:
                self.__raise_error(
                    f"Invalid token in krome format: {token}\n"
                    f"Supported tokens are {','.join(expected_tokens)}"
                )

        self.__raise_error("Invalid @format KROME declerative")

    def __handle_krome_var(self) -> None:
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__raise_error("Invalid KROME variable assignment detected")

        try:
            self.__globals[match.group("var").lower()] = parse_expr(
                f90_convert(match.group("expr").lower())
            )
        except (SyntaxError, NameError, TypeError):
            self.__logger.warning(
                f"Skipping variable: {match.group('var')}\n"
                f"at line: {self.__nline} since the expression is invalid sympy syntax"
            )

    def __handle_krome_var_errors(self):
        assert self.__matched_group is not None
        segment = self.__matched_group.group("segment")

        if segment is None:
            self.__raise_error("Empty segment after KROME @var declerative")

        segment = segment.strip()
        if not segment:
            self.__raise_error("Empty segment after KROME @var declerative")

        if "=" not in segment:
            self.__raise_error(
                "Invalid KROME @var declerative\n"
                "@var declerative must follow format: @var: varname=expression"
            )

        var_name, expr = segment.split("=", 1)
        var_name = var_name.strip()
        expr = expr.strip()

        if not var_name:
            self.__raise_error(
                "Invalid KROME @var declerative\nVariable name cannot be empty"
            )

        if not expr:
            self.__raise_error(
                "Invalid KROME @var declerative\nExpression cannot be empty"
            )

        self.__raise_error("Invalid KROME @var declerative")

    def __handle_prizmo_vars(self) -> None:
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__handle_prizmo_vars_errors()

        assert match is not None

        if match.group("begin"):
            self.__format_props["prizmo"]["parse_vars"] = True
            return

        if match.group("end"):
            self.__format_props["prizmo"]["parse_vars"] = False
            return

        if (
            match.group("var")
            and match.group("expr")
            and self.__format_props["prizmo"]["parse_vars"]
        ):
            try:
                self.__globals[match.group("var").lower()] = parse_expr(
                    f90_convert(match.group("expr").lower())
                )

            except (SyntaxError, NameError, TypeError):
                self.__logger.warning(
                    f"Skipping variable: {match.group('var')}\n"
                    f"at line: {self.__nline} since the expression is invalid sympy syntax"
                )

    def __handle_prizmo_vars_errors(self) -> None:
        assert self.__matched_group is not None
        segment = self.__matched_group.group("segment")
        assignment = self.__matched_group.group("assignment")

        if segment is None and assignment is None:
            self.__raise_error("Invalid PRIZMO variable section")

        if assignment is not None:
            if not self.__format_props["prizmo"]["parse_vars"]:
                self.__raise_error(
                    "PRIZMO variable assignment found outside VARIABLES block"
                )

            var_name, expr = assignment.split("=", 1)
            var_name = var_name.strip()
            expr = expr.strip()

            if not var_name.isidentifier():
                self.__raise_error(f"Invalid variable name '{var_name}'")

            if not expr:
                self.__raise_error("Expression cannot be empty")

        segment = segment.strip()
        if segment:
            self.__raise_error("Extra characters found after PRIZMO block declarative")

    def __handle_prizmo(self):
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__handle_prizmo_errors()

        reactants: str = match.group("reactants")
        products: str = match.group("products")
        tmin: str | None = match.group("tmin")
        tmax: str | None = match.group("tmax")
        rate: str = match.group("rate").strip()

        reactants = (
            reactants.replace("HE", "He")
            .replace(" E", " e-")
            .replace("E ", "e- ")
            .replace("GRAIN0", "GRAIN")
        )
        products = (
            products.replace("HE", "He")
            .replace(" E", " e-")
            .replace("E ", "e- ")
            .replace("GRAIN0", "GRAIN")
        )

        rr: list[str] = [r.strip() for r in reactants.split(" + ")]
        pp: list[str] = [p.strip() for p in products.split(" + ")]

        t_min: float | None = (
            float(tmin.strip().replace("d", "e")) if tmin and tmin.strip() else None
        )
        t_min = t_min if (t_min is not None and t_min > 0) else None

        t_max: float | None = (
            float(tmax.strip().replace("d", "e")) if tmax and tmax.strip() else None
        )
        t_max = t_max if (t_max is not None and t_max < 1e8) else None

        rate = rate.replace("user_crflux", "crate").replace("user_av", "av")

        self.__parsed_list.append(
            {
                "r": rr,
                "p": pp,
                "tmin": t_min,
                "tmax": t_max,
                "rate": rate,
                "string": self.__line.strip(),
            }
        )

    def __handle_prizmo_errors(self):
        self.__raise_error("Invalid PRIZMO reaction detected")

    def __handler_krome(self):
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__handle_krome_error()

        reactants: str = match.group("reactants")
        products: str = match.group("products")
        tmin: str = match.groupdict().get("tmin", "").strip().lower()
        tmax: str = match.groupdict().get("tmax", "").strip().lower()
        rate: str = match.groupdict().get("rate", "").strip()

        rr: list[str] = [r.strip() for r in reactants.split(",")[:-1]]
        pp: list[str] = [p.strip() for p in products.split(",")[:-1]]

        if len(rr) != self.__format_props["krome"]["nreact"]:
            self.__raise_error(
                "Invalid KROME line detected\n"
                f"Expected {self.__format_props['krome']['nreact']} reactants\n"
                f"from line {self.__format_props['krome']['format_nline']}.\n"
                f"Instead got {len(rr)} reactants"
            )

        if len(pp) != self.__format_props["krome"]["nprod"]:
            self.__raise_error(
                "Invalid KROME line detected\n"
                f"Expected {self.__format_props['krome']['nprod']} products \n"
                f"from line {self.__format_props['krome']['format_nline']}.\n"
                f"Instead got {len(pp)} products"
            )

        t_min: None | float = None
        t_max: None | float = None

        sp_reps = {"E": "e-", "e": "e-", "g": ""}
        rr = [sp_reps.get(r, r) for r in rr]
        pp = [sp_reps.get(p, p) for p in pp]

        sp_sreps = {"HE": "He"}

        for k, v in sp_sreps.items():
            rr = [x.replace(k, v) for x in rr]
            pp = [x.replace(k, v) for x in pp]

        rr = [r for r in rr if r != ""]
        pp = [p for p in pp if p != ""]

        tminmax_reps = {
            "d": "e",
            ".le.": "",
            ".ge.": "",
            ".lt.": "",
            ".gt.": "",
            ">": "",
            "<": "",
        }

        if tmin != "none" and tmin != "":
            for k, v in tminmax_reps.items():
                tmin = tmin.replace(k, v)
            t_min = float(tmin)

        if tmax != "none" and tmax != "":
            for k, v in tminmax_reps.items():
                tmax = tmax.replace(k, v)
            t_max = float(tmax)

        rate_reps = {
            "user_crflux": "crate",
            "user_crate": "crate",
            "user_av": "av",
        }
        for k, v in rate_reps.items():
            rate = rate.replace(k, v)

        rate = f90_convert(rate)
        if "auto" in rate:
            rate = rate.replace("auto", "PHOTO, 1e99")

        self.__parsed_list.append(
            {
                "r": rr,
                "p": pp,
                "tmin": t_min,
                "tmax": t_max,
                "rate": rate,
                "string": self.__line.strip(),
            }
        )

    def __handle_krome_error(self):
        assert self.__matched_group is not None

        segment = self.__matched_group.group("segment").lower()
        props = self.__format_props["krome"]
        num_fields = (
            int(props["idx"])
            + props["nreact"]
            + props["nreact"]
            + int(props["tmin"])
            + int(props["tmax"])
            + int(props["rate"])
        )
        num_fields_detected: int = segment.count(",") + 1

        if num_fields != num_fields_detected:
            self.__raise_error(
                "Number of fields in KROME reaction doesn't match\n"
                f"Number of fields detected: {num_fields_detected}\n"
                f"Number of fields expected: {num_fields}\n"
                + (
                    f"KROME format defined on line: {props['format_nline']}"
                    if props["format_nline"]
                    else ""
                )
            )

        if segment.count("r") != props["nreact"]:
            self.__raise_error(
                "Expected number of reactants did not match krome format\n"
                f"Number of reactants expected: {props['nreact']}\n"
                f"Number of reactants detected: {segment.count('r')}\n"
                + (
                    f"KROME format defined on line: {props['format_nline']}"
                    if props["format_nline"]
                    else ""
                )
            )

        if segment.count("p") != props["nprod"]:
            self.__raise_error(
                "Expected number of products did not match krome format\n"
                f"Number of products expected: {props['nprod']}\n"
                f"Number of products detected: {props['nprod']}\n"
                + (
                    f"KROME format defined on line: {props['format_nline']}"
                    if props["format_nline"]
                    else ""
                )
            )

        self.__raise_error("Invalid KROME reaction detected")

    def __handle_udfa(self):
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__handle_udfa_errors()

        ignore_species = {"CR", "CRP", "PHOTON", "CRPHOT", ""}

        rtype: str = match.group("rtype")
        reactants: str = match.group("reactants")
        products: str = match.group("products")
        ka: float = float(match.group("ka"))
        kb: float = float(match.group("kb"))
        kc: float = float(match.group("kc"))
        tmin: float = float(match.group("tmin"))
        tmax: float = float(match.group("tmax"))

        t_min: None | float = tmin if tmin > 0 else None
        t_max: None | float = tmax if tmax < 41000.0 else None

        rate_dict = {
            "CR": f"{kc:.2e} * crate",
            "PH": f"{ka:.2e} * exp(-{kc:.2f} * av)",
        }
        rate = f"{ka:.2e}"
        if kb:
            rate = f"{rate} * (tgas / 3e2)**({kb:.2f})"
        if kc:
            rate = f"{rate} * exp(-{kc:.2f} / tgas)"

        if rtype in rate_dict:
            rate = rate_dict[rtype]

        rr = [
            r.strip()
            for r in reactants.split(":")[:-1]
            if r.strip() not in ignore_species
        ]
        pp = [
            p.strip() for p in products.split(":")[:-1] if p.strip() not in ignore_species
        ]

        self.__parsed_list.append(
            {
                "r": rr,
                "p": pp,
                "tmin": t_min,
                "tmax": t_max,
                "rate": rate,
                "string": self.__line.strip(),
            }
        )

    def __handle_udfa_errors(self):
        self.__raise_error("Invalid UDFA reaction detected")

    def __handle_uclchem(self):
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__handle_uclchem_errors()

        reactants: str = match.group("reactants")
        products: str = match.group("products")
        ka: float = float(match.group("ka"))
        kb: float = float(match.group("kb"))
        kc: float = float(match.group("kc"))
        tmin: float = float(match.group("tmin"))
        tmax: float = float(match.group("tmax"))
        extrapolate: bool = match.group("extrapolate").strip().lower() == "true"

        ignore_species = {
            "CR",
            "CRP",
            "CRPHOT",
            "PHOTON",
            "NAN",
            "",
            "ER",
            "ERDES",
            "FREEZE",
            "H2FORM",
            "BULKSWAP",
            "DESCR",
            "DESOH2",
            "DEUVCR",
            "LH",
            "LHDES",
            "SURFSWAP",
            "THERM",
        }

        t_min: float = 3.0 if extrapolate else tmin
        t_max: float = 1e6 if extrapolate else tmax

        rr: list[str] = [
            self.__normalize_uclchem_species(r) for r in reactants.split(",")
        ]
        pp: list[str] = [
            self.__normalize_uclchem_species(p)
            for p in products.split(",")
            if p.strip().upper() not in ignore_species
        ]

        rate = "0.0"
        rate_dict = {
            "CRP": f"{ka:.2e} * crate",
            "CRPHOT": f"{ka:.2e} * (tgas/3e2)**({kb:.2f}) * crate",
            "PHOTON": f"{ka:.2e} * fuv * exp(-{kc:.2f} * av)",
            "FREEZE": f"(1e0 + {kb:.2e} * 1.671e-3/tgas/asize)*nuth*sigmah*sqrt(tgas/m)",
        }
        for r in rr:
            if r.upper() in rate_dict:
                rate = rate_dict[r.upper()]
                break
        rr = [r for r in rr if r.strip().upper() not in ignore_species]

        # FIXME: old parser sets rate = "0.0" at the very end
        rate = "0.0"

        self.__parsed_list.append(
            {
                "r": rr,
                "p": pp,
                "tmin": t_min,
                "tmax": t_max,
                "rate": rate,
                "string": self.__line.strip(),
            }
        )

    def __handle_uclchem_errors(self):
        self.__raise_error("Invalid UCLCHEM reaction detected")

    def __handle_kida(self):
        assert self.__local_pattern is not None
        match = self.__local_pattern.match(self.__line)
        if not match:
            self.__handle_kida_errors()

        reactants: str = match.group("reactants")
        products: str = match.group("products")
        ka: float = float(match.group("ka"))
        kb: float = float(match.group("kb"))
        kc: float = float(match.group("kc"))
        tmin: float = float(match.group("tmin"))
        tmax: float = float(match.group("tmax"))
        formula: int = int(match.group("formula"))

        t_min = tmin if tmin > 0 else None
        t_max = tmax if tmax < 9999.0 else None

        rates_dict = {
            1: f"{ka:.2e} * crate",
            2: f"{ka:.2e} * chi * exp(-{kc:.2e} * av)",
            3: f"{ka:.2e}"
            + (f" * (tgas / 300) ** ({kb:.2e})" if kb != 0.0 else "")
            + (f" * exp(-{kc:.2f} / tgas)" if kc != 0.0 else ""),
            4: f"{ka * kb:.2e}"
            + (f" * (0.62 + 0.4767 * {kc:2e} * sqrt(300 / tgas))" if kc != 0.0 else ""),
            5: f"{ka * kb:.2e}"
            + (
                f" * (1 + 0.0967 * {kc:.2e} * sqrt(300 / tgas + {kc**2:.2e} * 3e2 / 10.526 / tgas))"
                if kc != 0.0
                else ""
            ),
        }

        rate = rates_dict.get(formula, "0.0")

        ignore_species = {"cr", "crp", "photon"}
        rr = [
            r.strip()
            for r in reactants.split()
            if r != "+" and r.strip().lower() not in ignore_species
        ]
        pp = [
            p.strip()
            for p in products.split()
            if p != "+" and p.strip().lower() not in ignore_species
        ]

        self.__parsed_list.append(
            {
                "r": rr,
                "p": pp,
                "tmin": t_min,
                "tmax": t_max,
                "rate": rate,
                "string": self.__line.strip(),
            }
        )

    def __handle_kida_errors(self):
        self.__raise_error("Invalid KIDA reaction detected")

    @staticmethod
    def __normalize_uclchem_species(s: str):
        s = s.strip()
        if s.startswith("#"):
            s = s[1:] + "_DUST"
        if s.startswith("@"):
            s = s[1:] + "_BULK"
        if s == "E-":
            s = "e-"

        reps = {"HE": "He", "SI": "Si", "CL": "Cl", "MG": "Mg"}

        for k, v in reps.items():
            s = s.replace(k, v)

        return s

    def __set_known_replacments(self) -> None:
        # Some krome replacements
        # Order matters here
        # Expressions with dependencies must come first
        replacements = {
            "invt32": "1e0 / t32",
            "invte": "1e0 / te",
            "t32": "tgas/3e2",
            "te": "tgas*8.617343e-5",
            "invtgas": "1e0 / tgas",
            "sqrtgas": "sqrt(tgas)",
            "user_tdust": "tdust",
            "user_av": "av",
            "get_hnuclei(n)": "nh",
            "n(idx_h2)": "nh2",
            "n(idx_h)": "nh0",
            "n_global(idx_h2)": "nh2",
        }

        for k, v in replacements.items():
            self.__globals[k] = parse_expr(v)

    def __normalize_rates(self):
        for r in self.__parsed_list:
            assert isinstance(r["rate"], str)
            r["rate"] = r["rate"].lower()

    def __global_patterns_dict(self) -> dict[str, patternProps]:
        patterns: dict = {
            "krome_format": {
                "global_re": r"^\s*@format\s*:(?P<format>.*?)$",
                "local_re": (
                    r"^\s*@format\s*:\s*"
                    r"(?P<idx>(?i:idx)\s*,\s*)?"
                    r"(?P<reactants>(?:(?i:R)\s*,\s*)+)"
                    r"(?P<products>(?:(?i:P)\s*,\s*)+)"
                    r"(?P<tmin>(?i:tmin)\s*,?\s*)?"
                    r"(?P<tmax>(?i:tmax)\s*,?\s*)?"
                    r"(?P<rate>(?i:rate)\s*)?\s*$"
                ),
                "handler": self.__handle_krome_format,
            },
            "krome_var": {
                "global_re": r"^\s*@var\s*:(?P<segment>.*?)$",
                "local_re": (
                    r"^\s*@var\s*:\s*"
                    r"(?P<var>\w+)"
                    r"\s*=\s*"
                    r"\s*(?P<expr>.*?)\s*$"
                ),
                "handler": self.__handle_krome_var,
            },
            "prizmo_vars": {
                "global_re": (
                    r"^\s*(?:"
                    r"(?:(?i:variables)\s*\{|\})(?P<segment>.*?)"
                    r"|"
                    r"(?P<assignment>\w+\s*=.*?)"
                    r")\s*$"
                ),
                "local_re": (
                    r"^\s*(?P<begin>(?i:variables)\s*\{)\s*$"
                    r"|"
                    r"^\s*(?P<end>\}\s*)$"
                    r"|"
                    r"^\s*(?P<var>\w+)"
                    r"\s*=\s*"
                    r"\s*(?P<expr>.*?)\s*$"
                ),
                "handler": self.__handle_prizmo_vars,
            },
            "prizmo": {
                "global_re": r"^(?!\s*[!#]).*->.*$",
                "local_re": (
                    r"^\s*"
                    r"(?P<reactants>[\w\+\-\s]+)"
                    r"\s*->\s*"
                    r"(?P<products>[\w\+\-\s]+)"
                    r"\s*\[\s*"
                    r"(?P<tmin>[^,\]]*)?"
                    r"\s*,?\s*"
                    r"(?P<tmax>[^,\]]*)?"
                    r"\s*\]\s*"
                    r"(?P<rate>.*)"
                    r"\s*$"
                ),
                "handler": self.__handle_prizmo,
            },
            "udfa": {
                "global_re": r"^(?!\s*[!#@]).*:.*$",
                "local_re": (
                    r"^\s*\d+\s*:"
                    r"\s*(?P<rtype>[^:]*?)\s*:"
                    r"\s*(?P<reactants>(?:[^:]*:){2})"
                    r"\s*(?P<products>(?:[^:]*:){4})"
                    r"\s*(?P<flag>[^:]*)\s*:"
                    r"\s*(?P<ka>[^:]*)\s*:"
                    r"\s*(?P<kb>[^:]*)\s*:"
                    r"\s*(?P<kc>[^:]*)\s*:"
                    r"\s*(?P<tmin>[^:]*)\s*:"
                    r"\s*(?P<tmax>[^:]*?)(?:\s*:.*)?$"
                ),
                "handler": self.__handle_udfa,
            },
            "krome": {
                "global_re": (
                    r"^(?!\s*[!#@])"
                    r"(?!.*,\s*(?i:NAN)\s*(?:,|$))"
                    r"(?=.*,)"
                    r"(?P<segment>.*)$"
                ),
                "local_re": (
                    r"^\s*"
                    r"(?!.*,\s*(?i:NAN)\s*(?:,|$))"
                    + (
                        r"(?P<idx>[^,]*)\s*,\s*"
                        if self.__format_props["krome"]["idx"]
                        else ""
                    )
                    + rf"(?P<reactants>(?:[^,]*\s*,\s*){{{self.__format_props['krome']['nreact']}}})"
                    + rf"(?P<products>(?:[^,]*\s*,\s*){{{self.__format_props['krome']['nprod']}}})"
                    + (
                        r"(?P<tmin>[^,]*)\s*,\s*"
                        if self.__format_props["krome"]["tmin"]
                        else ""
                    )
                    + (
                        r"(?P<tmax>[^,]*)\s*,\s*"
                        if self.__format_props["krome"]["tmax"]
                        else ""
                    )
                    + (r"(?P<rate>.*)" if self.__format_props["krome"]["rate"] else "")
                    + r"\s*$"
                ),
                "handler": self.__handler_krome,
            },
            "uclchem": {
                "global_re": (r"^(?!\s*[!]|(?:\s*#\s)).*,\s*(?i:NAN)\s*(?:,|$)"),
                "local_re": (
                    r"^\s*"
                    r"(?=.*,\s*(?i:NAN)\s*(?:,|$))"
                    r"(?P<reactants>(?:[#@\w\d\+-]*\s*,\s*){3})"
                    r"(?P<products>(?:[#@\w\d\+-]*\s*,\s*){4})"
                    r"(?P<ka>[^,]*)\s*,\s*"
                    r"(?P<kb>[^,]*)\s*,\s*"
                    r"(?P<kc>[^,]*)\s*,\s*"
                    r"(?P<tmin>[^,]*)\s*,\s*"
                    r"(?P<tmax>[^,]*)\s*,\s*"
                    r"(?P<extrapolate>.*?)"
                    r"\s*$"
                ),
                "handler": self.__handle_uclchem,
            },
            "kida": {
                "global_re": r"^(?!\s*[!#@]).{34}.{57}",
                "local_re": (
                    r"^(?P<reactants>.{34})"
                    r"(?P<products>.{57})"
                    r"\s*(?P<ka>[^\s]+)"
                    r"\s*(?P<kb>[^\s]+)"
                    r"\s*(?P<kc>[^\s]+)"
                    r"\s*[^\s]+\s*[^\s]+\s*[^\s]+\s*[^\s]+"
                    r"\s*(?P<tmin>[^\s]+)"
                    r"\s*(?P<tmax>[^\s]+)"
                    r"\s*(?P<formula>[^\s]+)"
                    r".*$"
                ),
                "handler": self.__handle_kida,
            },
        }

        return {
            key: {
                "global_re": re.compile(value["global_re"]),
                "local_re": re.compile(value["local_re"]),
                "handler": value["handler"],
            }
            for key, value in patterns.items()
        }
