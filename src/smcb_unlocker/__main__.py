from concurrent.futures import ThreadPoolExecutor
import logging
import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from smcb_unlocker.config import Config
from smcb_unlocker.logging import configure_google_logging, configure_simple_logging
from smcb_unlocker.pipeline import LogExportPipeline, RebootPipeline, SmcbUnlockPipeline


log = logging.getLogger(__name__)


def configure_logging(config: Config):
    if config.log_format == "simple":
        configure_simple_logging(config.log_level)
    elif config.log_format == "google":
        configure_google_logging(config.log_level)
    else:
        raise ValueError(f"Unknown log format: {config.log_format}")

    # Disable httpx INFO level logging to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    config = Config()
    configure_logging(config)
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        environment=config.sentry_environment,
        release=config.sentry_release or os.environ.get("SENTRY_RELEASE"),
        integrations=[
            LoggingIntegration(
                level=logging.WARNING,       # breadcrumbs from WARNING+
                event_level=logging.CRITICAL, # only CRITICAL creates events
            ),
        ],
    )

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
