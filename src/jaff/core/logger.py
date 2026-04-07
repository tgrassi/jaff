import logging

import colorlog
from tqdm import tqdm


class TqdmHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)


class JaffLogger:
    def __init__(self, name: str = "JAFF", level: int = logging.INFO):
        self.logger = logging.getLogger(name)

        if not self.logger.handlers:
            handler = TqdmHandler()

            formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)s:%(reset)s %(message)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.setLevel(level)
        self.logger.propagate = False

    def get_logger(self):
        return self.logger
