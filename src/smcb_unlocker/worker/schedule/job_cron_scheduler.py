import asyncio
from datetime import datetime
from typing import TypeVar, Generic

from cronsim import CronSim

from smcb_unlocker.sentry_checkins import SentryCheckins


T = TypeVar('T')


class JobCronScheduler(Generic[T]):
    job_factory: callable[[], T]
    cron_expression: str
    sentry_checkins: SentryCheckins | None

    job_queue: asyncio.Queue[T]

    def __init__(self, job_factory: callable[[], T], cron_expression: str, sentry_checkins: SentryCheckins | None = None):
        self.job_factory = job_factory
        self.cron_expression = cron_expression
        self.sentry_checkins = sentry_checkins

        self.job_queue = None

    def connectOutput(self, job_queue: asyncio.Queue[T]):
        self.job_queue = job_queue

    def ensure_connected(self):
        if not self.job_queue:
            raise RuntimeError("JobCronScheduler is not connected. Call 'connectOutput' method first.")

    async def run(self):
        self.ensure_connected()
        iterator = CronSim(self.cron_expression, datetime.now())

        while True:
            next_run = next(iterator)
            wait_seconds = (next_run - datetime.now()).total_seconds()
            await asyncio.sleep(wait_seconds)

            job = self.job_factory()
            if self.sentry_checkins:
                self.sentry_checkins.in_progress(job)
            
            await self.job_queue.put(job)
