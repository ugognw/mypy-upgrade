import logging
import sys
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
        fmt: "str | None" = None,
        datefmt: "str | None" = None,
        style: "_FormatStyle" = "%",
        validate: bool = True,  # noqa: FBT001, FBT002
        *,
        defaults: "dict[str, Any] | None" = None,
        colours: "dict[int, int] | None" = None,
    ) -> None:
        self.colours = colours or DEFAULT_COLOURS
        kwargs: dict[str, Any] = {}

        if sys.version_info >= (3, 8):
            super().__init__(fmt, datefmt, style, validate=validate)
            if sys.version_info >= (3, 10):
                kwargs["validate"] = validate

                super().__init__(
                    fmt, datefmt, style, validate=validate, defaults=defaults
                )
        else:
            super().__init__(fmt, datefmt, style)

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802
        colour_code = self.colours[record.levelno]
        return f"\033[1;{colour_code}m{self._style.format(record)}\033[0m"
