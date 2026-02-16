import asyncio
import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

import httpx
import sentry_sdk

from smcb_unlocker.sentry_checkins import SentryCheckins


T = TypeVar("T")

log = logging.getLogger(__name__)


class BaseWorker(ABC, Generic[T]):
    sentry_checkins: SentryCheckins | None
    _job_queue: asyncio.Queue[T] | None

    def __init__(self, sentry_checkins: SentryCheckins | None = None):
        self.sentry_checkins = sentry_checkins
        self._job_queue = None

    def connect_job_queue(self, job_queue: asyncio.Queue[T]):
        self._job_queue = job_queue

    @abstractmethod
    async def handle(self, job: T) -> None: ...

    async def run(self):
        if not self._job_queue:
            raise RuntimeError(f"{type(self).__name__} is not connected. Call 'connect_job_queue' first.")

        while True:
            job = await self._job_queue.get()

            try:
                log.info("Start job", extra={"job": job})
                await self.handle(job)
                log.info("End job", extra={"job": job})
                if self.sentry_checkins:
                    self.sentry_checkins.ok(job)
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                log.warning("Konnektor unreachable: %s", e, extra={"job": job})
                if self.sentry_checkins:
                    self.sentry_checkins.error(job)
            except Exception as e:
                log.exception("Error during job", extra={"job": job})
                sentry_sdk.capture_exception(e)
                if self.sentry_checkins:
                    self.sentry_checkins.error(job)

            self._job_queue.task_done()
