import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import _FormatStyle


DEFAULT_COLOURS = {
    logging.DEBUG: 36,
    logging.INFO: 33,
    logging.WARNING: 95,
    logging.ERROR: 35,
    logging.CRITICAL: 31,
}


class ColouredFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: "_FormatStyle" = "%",
        validate: bool = True,  # noqa: FBT001, FBT002
        *,
        defaults: Mapping[str, Any] | None = None,
        colours: dict[int, str] | None = None,
    ) -> None:
        self.colours = colours or DEFAULT_COLOURS
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def formatMessage(self, record: logging.LogRecord):  # noqa: N802
        colour_code = self.colours[record.levelno]
        return f"\033[1;{colour_code}m{self._style.format(record)}\033[0m"
