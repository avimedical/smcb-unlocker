import logging
from logging import Formatter, StreamHandler


SIMPLE_LOG_FORMAT = "%(levelname)s:%(name)s:%(job)s:%(message)s"


def configure_simple_logging(level: str):
    handler = StreamHandler()
    handler.setFormatter(Formatter(SIMPLE_LOG_FORMAT, defaults={ "job": None }))
    logging.basicConfig(level=level, handlers=[handler])
