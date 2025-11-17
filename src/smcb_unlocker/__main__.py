from concurrent.futures import ThreadPoolExecutor
import dataclasses
import logging
import sys

from google.cloud.logging.handlers import StructuredLogHandler
import sentry_sdk

from smcb_unlocker.client.konnektor.admin.model import ProtocolEntry
from smcb_unlocker.config import Config
from smcb_unlocker.pipeline import LogExportPipeline, RebootPipeline, SmcbUnlockPipeline


log = logging.getLogger(__name__)


class GoogleCloudLoggingJsonFieldsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        json_fields = record.__dict__.get("json_fields", {})

        if hasattr(record, "job"):
            if dataclasses.is_dataclass(record.job):
                job_dict = { field.name: getattr(record.job, field.name) for field in dataclasses.fields(record.job) if field.repr }
                job_dict["type"] = type(record.job).__name__
                json_fields["job"] = job_dict
            else:
                json_fields["job"] = str(record.job)

        if hasattr(record, "protocol"):
            if isinstance(record.protocol, ProtocolEntry):
                json_fields["protocol"] = record.protocol.model_dump()
            else:
                json_fields["protocol"] = str(record.protocol)

        record.json_fields = json_fields
        return super().filter(record)


def configure_logging(config: Config):
    if config.log_format == "simple":
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(job)s:%(message)s", defaults={ "job": None }))
        logging.basicConfig(level=config.log_level, handlers=[handler])
    elif config.log_format == "google":
        handler = StructuredLogHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.addFilter(GoogleCloudLoggingJsonFieldsFilter())
        logging.basicConfig(level=config.log_level, handlers=[handler])

    # Disable httpx INFO level logging to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    config = Config()
    configure_logging(config)
    sentry_sdk.init(dsn=config.sentry_dsn, environment=config.sentry_environment)

    pipelines = [
        LogExportPipeline(config),
        SmcbUnlockPipeline(config),
        RebootPipeline(config),
    ]

    with ThreadPoolExecutor(max_workers=len(pipelines), thread_name_prefix="pipeline") as executor:
        for pipeline in pipelines:
            executor.submit(pipeline.run)


if __name__ == "__main__":
    main()
