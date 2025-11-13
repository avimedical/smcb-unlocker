import asyncio
from typing import TypeVar, Generic

from sentry_sdk.crons import monitor


T = TypeVar('T')


class JobIntervalScheduler(Generic[T]):
    job_factory: callable[[], T]
    interval: int
    monitor_slug: str | None

    job_queue: asyncio.Queue[T]

    def __init__(self, job_factory: callable[[], T], interval: int, monitor_slug: str | None = None):
        self.job_factory = job_factory
        self.interval = interval
        self.monitor_slug = monitor_slug
        self.job_queue = None

    def connectOutput(self, job_queue: asyncio.Queue[T]):
        self.job_queue = job_queue

    async def run(self):
        while True:
            with monitor(self.monitor_slug):
                job = self.job_factory()
                await self.job_queue.put(job)
            
            await asyncio.sleep(self.interval)
