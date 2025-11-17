import asyncio
import uuid

from smcb_unlocker.config import Config
from smcb_unlocker.job import RebootJob
from smcb_unlocker.worker import JobCronScheduler, RebootWorker
from smcb_unlocker.sentry_checkins import SentryCheckins


class RebootPipeline:
    config: Config

    def __init__(self, config: Config):
        self.config = config

    async def coroutine(self):
        sentry_checkins = SentryCheckins(self.config.sentry_monitor_slug_prefix) if self.config.sentry_monitor_slug_prefix else None

        job_queue: asyncio.Queue[RebootJob] = asyncio.Queue(self.config.reboot_queue_size)
        schedulers: list[JobCronScheduler[RebootJob]] = [
            JobCronScheduler(
                lambda: RebootJob(str(uuid.uuid4()), konnektor_name, konnektor_config.base_url),
                cron_expression=konnektor_config.reboot_cron,
                sentry_checkins=sentry_checkins
            )
            for konnektor_name, konnektor_config in self.config.konnektors.items() if konnektor_config.reboot_cron
        ]
        workers = [
            RebootWorker(self.config.credentials, sentry_checkins=sentry_checkins)
            for _ in range(self.config.reboot_workers)
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
