import asyncio
import logging

import httpx

from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials
from smcb_unlocker.job import LogExportJob
from smcb_unlocker.sentry_checkins import SentryCheckins


log = logging.getLogger(__name__)


class LogExportWorker:
    credentials: ConfigCredentials
    sentry_checkins: SentryCheckins | None

    log_job_queue: asyncio.Queue[LogExportJob] | None

    def __init__(self, credentials: ConfigCredentials, sentry_checkins: SentryCheckins | None = None):
        self.credentials = credentials
        self.sentry_checkins = sentry_checkins
        self.log_job_queue = None

    def connectInput(self, log_job_queue: asyncio.Queue[LogExportJob]):
        self.log_job_queue = log_job_queue

    def ensure_connected(self):
        if not self.log_job_queue:
            raise RuntimeError("LogExportWorker is not connected. Call 'connectInput' method first.")

    async def handle(self, job: LogExportJob):
        # Placeholder for actual log export logic
        log.info(f"Exporting log data", extra={"job": job})
        await asyncio.sleep(0.1)  # Simulate some async work

    async def run(self):
        self.ensure_connected()
        while True:
            job = await self.log_job_queue.get()
            
            try:
                log.info(f"Start job", extra={"job": job})

                await self.handle(job)

                log.info(f"End job", extra={"job": job})
                if self.sentry_checkins:
                    self.sentry_checkins.ok(job)
            except Exception as e:
                log.exception(f"Error during job", extra={"job": job})
                if self.sentry_checkins:
                    self.sentry_checkins.error(job)
            
            self.log_job_queue.task_done()
