import atexit
import logging
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


class JaffProgress(Progress):
    def track(
        self,
        sequence: Sequence[ProgressType] | Iterable[ProgressType],
        total: Optional[float] = None,
        task_id: Optional[TaskID] = None,
        description: str = "Working...",
        update_period: float = 0.1,
    ) -> Iterable[ProgressType]:
        for task in list(self.tasks):
            if task.finished:
                self.remove_task(task.id)

        if total is None and hasattr(sequence, "__len__"):
            total = len(sequence)
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


jaff_console = Console()

jaff_progress = JaffProgress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=None),
    MofNCompleteColumn(),
    TimeElapsedColumn(),
    console=jaff_console,
    expand=True,
)

jaff_progress.start()
atexit.register(jaff_progress.stop)


class JaffLogger:
    def __init__(self, name: str = "JAFF", level: int = logging.INFO):
        self.logger = logging.getLogger(name)

        if not self.logger.handlers:
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
