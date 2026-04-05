from pathlib import Path


class ParserError(Exception):
    def __init__(
        self,
        message: str,
        line: str | None = None,
        nline: int | None = None,
        fname: str | Path | None = None,
        funcname: str | None = None,
    ):
        self.message = message
        self.line = line
        self.nline = nline
        self.fname = fname
        self.funcname = funcname

        if fname is None and isinstance(nline, int):
            raise AttributeError(
                "File name must be specified if line number is specified"
            )

        super().__init__(self.__format_message())

    def __format_message(self) -> str:
        error_str: str = ""

        if self.funcname is not None:
            error_str += f"Function: {self.funcname}\n"

        if self.fname is not None:
            error_str += f"File: {self.fname}\n"

        if self.nline is not None:
            error_str += f"Line number: {self.nline}\n"

        if self.line is not None:
            error_str += f"Line: {self.line}\n"

        error_str += self.message

        return error_str
