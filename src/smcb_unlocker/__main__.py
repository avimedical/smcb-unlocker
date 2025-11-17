import asyncio
import dataclasses
import logging
import sys
import uuid

from google.cloud.logging.handlers import StructuredLogHandler
import sentry_sdk

from smcb_unlocker.client.konnektor.admin.model import ProtocolEntry
from smcb_unlocker.config import Config
from smcb_unlocker.job import DiscoverLockedSmcbJob, LogExportJob, SmcbVerifyJob
from smcb_unlocker.sentry_checkins import SentryCheckins
from smcb_unlocker.worker.discover.discover_locked_smcb_worker import DiscoverLockedSmcbWorker
from smcb_unlocker.worker.schedule.job_interval_scheduler import JobIntervalScheduler
from smcb_unlocker.worker.log.log_export_worker import LogExportWorker
from smcb_unlocker.worker.verify.smcb_verify_worker import SmcbVerifyWorker


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


async def main():
    config = Config()

    configure_logging(config)

    sentry_sdk.init(dsn=config.sentry_dsn, environment=config.sentry_environment)
    sentry_checkins = SentryCheckins(config.sentry_monitor_slug_prefix) if config.sentry_monitor_slug_prefix else None

    # SMC-B unlocking pipeline

    discover_job_queue: asyncio.Queue[DiscoverLockedSmcbJob] = asyncio.Queue(config.discover_queue_size)
    verify_job_queue: asyncio.Queue[SmcbVerifyJob] = asyncio.Queue(config.verify_queue_size)
    
    discover_schedule_workers: list[JobIntervalScheduler[DiscoverLockedSmcbJob]] = [
        JobIntervalScheduler(
            lambda: DiscoverLockedSmcbJob(str(uuid.uuid4()), konnektor_name, konnektor_config.base_url),
            interval=konnektor_config.interval,
            sentry_checkins=sentry_checkins
        )
        for konnektor_name, konnektor_config in config.konnektors.items()
    ]
    discover_workers = [
        DiscoverLockedSmcbWorker(config.credentials, sentry_checkins=sentry_checkins)
        for _ in range(config.discover_workers)
    ]
    verify_workers = [
        SmcbVerifyWorker(config.credentials, sentry_checkins=sentry_checkins)
        for _ in range(config.verify_workers)
    ]

    for scheduler in discover_schedule_workers:
        scheduler.connectOutput(discover_job_queue)
    for discover_worker in discover_workers:
        discover_worker.connectInput(discover_job_queue)
        discover_worker.connectOutput(verify_job_queue)
    for verify_worker in verify_workers:
        verify_worker.connectInput(verify_job_queue)

    # Log export pipeline

    log_export_job_queue: asyncio.Queue[LogExportJob] = asyncio.Queue(config.log_export_queue_size)
    log_export_schedule_workers: list[JobIntervalScheduler[LogExportJob]] = [
        JobIntervalScheduler(
            lambda: LogExportJob(str(uuid.uuid4()), konnektor_name, konnektor_config.base_url),
            interval=konnektor_config.log_export_interval,
            sentry_checkins=sentry_checkins
        )
        for konnektor_name, konnektor_config in config.konnektors.items()
    ]
    log_export_workers = [
        LogExportWorker(config.credentials, sentry_checkins=sentry_checkins)
        for _ in range(config.log_export_workers)
    ]
    for scheduler in log_export_schedule_workers:
        scheduler.connectOutput(log_export_job_queue)
    for log_export_worker in log_export_workers:
        log_export_worker.connectInput(log_export_job_queue)

    async with asyncio.TaskGroup() as tg:
        if sentry_checkins:
            tg.create_task(sentry_checkins.cleanup_orphaned_checkins())

        for scheduler in discover_schedule_workers:
            tg.create_task(scheduler.run())
        for discover_locked_smcb_worker in discover_workers:
            tg.create_task(discover_locked_smcb_worker.run())
        for smcb_verify_worker in verify_workers:
            tg.create_task(smcb_verify_worker.run())

        for scheduler in log_export_schedule_workers:
            tg.create_task(scheduler.run())
        for log_export_worker in log_export_workers:
            tg.create_task(log_export_worker.run())


if __name__ == "__main__":
    asyncio.run(main())
