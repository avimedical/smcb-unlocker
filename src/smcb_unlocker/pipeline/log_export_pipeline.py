import asyncio
from functools import partial
import uuid

from smcb_unlocker.config import Config
from smcb_unlocker.job import LogExportJob
from smcb_unlocker.worker import JobIntervalScheduler, LogExportWorker
from smcb_unlocker.sentry_checkins import SentryCheckins


class LogExportPipeline:
    config: Config

    def __init__(self, config: Config):
        self.config = config

    async def coroutine(self):
        sentry_checkins = SentryCheckins(self.config.sentry_monitor_slug_prefix) if self.config.sentry_monitor_slug_prefix else None

        job_queue: asyncio.Queue[LogExportJob] = asyncio.Queue(self.config.log_export_queue_size)
        schedulers: list[JobIntervalScheduler[LogExportJob]] = [
            JobIntervalScheduler(
                partial(LogExportJob, job_id=str(uuid.uuid4()), konnektor_name=konnektor_name, konnektor_base_url=konnektor_config.base_url),
                interval=konnektor_config.log_export_interval,
                sentry_checkins=sentry_checkins
            )
            for konnektor_name, konnektor_config in self.config.konnektors.items()
        ]
        workers = [
            LogExportWorker(self.config.credentials, timeout=self.config.httpx_timeout, sentry_checkins=sentry_checkins)
            for _ in range(self.config.log_export_workers)
        ]
        
        for scheduler in schedulers:
            scheduler.connectOutput(job_queue)
        for worker in workers:
            worker.connectInput(job_queue)

        async with asyncio.TaskGroup() as tg:
            if sentry_checkins:
                tg.create_task(sentry_checkins.cleanup_orphaned_checkins())
            for scheduler in schedulers:
                tg.create_task(scheduler.run())
            for worker in workers:
                tg.create_task(worker.run())

    def run(self):
        asyncio.run(self.coroutine())
