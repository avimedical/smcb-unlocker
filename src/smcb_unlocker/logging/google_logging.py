import logging
import sys

from google.cloud.logging.handlers import StructuredLogHandler

from smcb_unlocker.logging.filter import GoogleCloudLoggingJsonFieldsFilter


GOOGLE_LOG_FORMAT = "%(message)s"


def configure_google_logging(level: str):
    handler = StructuredLogHandler(stream=sys.stdout)
    formatter = logging.Formatter(GOOGLE_LOG_FORMAT)
    filter = GoogleCloudLoggingJsonFieldsFilter()

    handler.setFormatter(formatter)
    handler.addFilter(filter)
    
    logging.basicConfig(level=level, handlers=[handler])
