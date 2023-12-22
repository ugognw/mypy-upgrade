import logging
from logging import _Level


class MessagesHandler(logging.Handler):
    def __init__(self, level: _Level = 0) -> None:
        self.messages = []
        super().__init__(level)

    def emit(self, record):
        self.messages.append(self.format(record))
