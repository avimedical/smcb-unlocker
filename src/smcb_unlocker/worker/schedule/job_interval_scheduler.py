import asyncio
from typing import TypeVar, Generic

from smcb_unlocker.sentry_checkins import SentryCheckins


T = TypeVar('T')


class JobIntervalScheduler(Generic[T]):
    job_factory: callable[[], T]
    interval: int
    sentry_checkins: SentryCheckins | None

    job_queue: asyncio.Queue[T]

    def __init__(self, job_factory: callable[[], T], interval: int, sentry_checkins: SentryCheckins | None = None):
        self.job_factory = job_factory
        self.interval = interval
        self.sentry_checkins = sentry_checkins

        self.job_queue = None

    def connectOutput(self, job_queue: asyncio.Queue[T]):
        self.job_queue = job_queue

    async def run(self):
        while True:
            job = self.job_factory()
            if self.sentry_checkins:
                self.sentry_checkins.in_progress(job)
            
            await self.job_queue.put(job)
            await asyncio.sleep(self.interval)
