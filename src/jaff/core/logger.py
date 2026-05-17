import atexit
import logging
import os
import sys
from contextlib import contextmanager
from typing import Iterable, Optional, Sequence

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressType,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text
from rich.traceback import install


def _is_jupyter() -> bool:
    try:
        shell = get_ipython().__class__.__name__  # type: ignore
        return shell == "ZMQInteractiveShell"
    except NameError:
        return False


IN_JUPYTER = _is_jupyter()
# True when running inside a Jupyter kernel OR as a subprocess launched from one.
# Jupyter kernels export JPY_PARENT_PID; child processes inherit it.
_IN_JUPYTER_ENV = IN_JUPYTER or "JPY_PARENT_PID" in os.environ

_PROGRESS_KWARGS = dict(
    expand=True,
    redirect_stdout=False,
    redirect_stderr=False,
    transient=True,
)


def _make_progress_columns():
    return (
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    )


def _make_progress(console: Console, auto_refresh: bool = True) -> Progress:
    return Progress(
        *_make_progress_columns(),
        console=console,
        auto_refresh=auto_refresh,
        **_PROGRESS_KWARGS,
    )


class JaffProgress(Progress):
    @contextmanager
    def indeterminate(self, description: str):
        if IN_JUPYTER:
            with _make_progress(self.console) as p:
                task_id = p.add_task(description, total=None)
                yield task_id
        elif _IN_JUPYTER_ENV:
            yield None
        else:
            task_id = self.add_task(description, total=None)
            try:
                yield task_id
            finally:
                self.remove_task(task_id)

    def track(
        self,
        sequence: Sequence[ProgressType] | Iterable[ProgressType],
        total: Optional[float] = None,
        task_id: Optional[TaskID] = None,
        *args,
        description: str = "Working...",
        update_period: float = 0.1,
        **kwargs,
    ) -> Iterable[ProgressType]:
        if IN_JUPYTER:
            with _make_progress(self.console, auto_refresh=False) as p:
                if total is None and hasattr(sequence, "__len__"):
                    total = len(sequence)  # type: ignore
                task_id = p.add_task(description, total=total)
                _get_time = p.get_time
                last_time = _get_time()
                for value in sequence:
                    yield value
                    p.advance(task_id, 1)
                    current_time = _get_time()
                    if (current_time - last_time) > update_period:
                        p.refresh()
                        last_time = current_time
                p.update(task_id, completed=total)
                p.refresh()
            return

        if _IN_JUPYTER_ENV:
            for value in sequence:
                yield value
            return

        for task in list(self.tasks):
            if task.finished:
                self.remove_task(task.id)

        if total is None and hasattr(sequence, "__len__"):
            total = len(sequence)  # type: ignore
        task_id = self.add_task(description, total=total)
        _finished = False
        try:
            _get_time = self.get_time
            last_time = _get_time()
            for value in sequence:
                yield value
                current_time = _get_time()
                if (current_time - last_time) > update_period:
                    self.advance(task_id, 1)
                    self.refresh()
                    last_time = current_time
                else:
                    self.advance(task_id, 1)
            _finished = True
            self.update(task_id, completed=total)
            self.refresh()
        finally:
            if not _finished:
                self.remove_task(task_id)


jaff_console = Console(force_jupyter=IN_JUPYTER)
install(console=jaff_console, show_locals=False)

jaff_progress = JaffProgress(
    *_make_progress_columns(), console=jaff_console, **_PROGRESS_KWARGS
)

if not _IN_JUPYTER_ENV:
    jaff_progress.start()
    atexit.register(jaff_progress.stop)


class _StripMarkupFormatter(logging.Formatter):
    """Strip Rich markup tags from log messages for plain-text output."""

    def format(self, record: logging.LogRecord) -> str:
        original_msg, original_args = record.msg, record.args
        record.msg = Text.from_markup(record.getMessage()).plain
        record.args = None
        result = super().format(record)
        record.msg, record.args = original_msg, original_args
        return result


class JaffLogger:
    def __init__(self, name: str = "JAFF", level: int = logging.INFO):
        self.logger = logging.getLogger(name)

        if not self.logger.handlers:
            if _IN_JUPYTER_ENV:
                handler: logging.Handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(_StripMarkupFormatter("%(levelname)-8s %(message)s"))
            else:
                handler = RichHandler(
                    console=jaff_console,
                    rich_tracebacks=True,
                    markup=True,
                    show_time=False,
                )
                handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

        self.logger.setLevel(level)
        self.logger.propagate = False

    def get_logger(self):
        return self.logger
