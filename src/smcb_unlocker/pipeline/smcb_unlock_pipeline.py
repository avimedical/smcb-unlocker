import asyncio
import uuid

from smcb_unlocker.config import Config
from smcb_unlocker.job import DiscoverLockedSmcbJob, SmcbVerifyJob
from smcb_unlocker.worker import DiscoverLockedSmcbWorker, JobIntervalScheduler, SmcbVerifyWorker
from smcb_unlocker.sentry_checkins import SentryCheckins


class SmcbUnlockPipeline:
    config: Config

    def __init__(self, config: Config):
        self.config = config

    async def coroutine(self):
        sentry_checkins = SentryCheckins(self.config.sentry_monitor_slug_prefix) if self.config.sentry_monitor_slug_prefix else None

        discover_job_queue: asyncio.Queue[DiscoverLockedSmcbJob] = asyncio.Queue(self.config.discover_queue_size)
        verify_job_queue: asyncio.Queue[SmcbVerifyJob] = asyncio.Queue(self.config.verify_queue_size)
        
        discover_schedule_workers: list[JobIntervalScheduler[DiscoverLockedSmcbJob]] = [
            JobIntervalScheduler(
                lambda: DiscoverLockedSmcbJob(str(uuid.uuid4()), konnektor_name, konnektor_config.base_url),
                interval=konnektor_config.interval,
                sentry_checkins=sentry_checkins
            )
            for konnektor_name, konnektor_config in self.config.konnektors.items()
        ]
        discover_workers = [
            DiscoverLockedSmcbWorker(self.config.credentials, sentry_checkins=sentry_checkins)
            for _ in range(self.config.discover_workers)
        ]
        verify_workers = [
            SmcbVerifyWorker(self.config.credentials, sentry_checkins=sentry_checkins)
            for _ in range(self.config.verify_workers)
        ]

        for scheduler in discover_schedule_workers:
            scheduler.connectOutput(discover_job_queue)
        for discover_worker in discover_workers:
            discover_worker.connectInput(discover_job_queue)
            discover_worker.connectOutput(verify_job_queue)
        for verify_worker in verify_workers:
            verify_worker.connectInput(verify_job_queue)

        async with asyncio.TaskGroup() as tg:
            if sentry_checkins:
                tg.create_task(sentry_checkins.cleanup_orphaned_checkins())
            for scheduler in discover_schedule_workers:
                tg.create_task(scheduler.run())
            for discover_worker in discover_workers:
                tg.create_task(discover_worker.run())
            for verify_worker in verify_workers:
                tg.create_task(verify_worker.run())

    def run(self):
        asyncio.run(self.coroutine())
