import asyncio
from datetime import datetime, timedelta
import logging

import httpx
import sentry_sdk

from smcb_unlocker.client.konnektor.admin import login, ping, reboot
from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials
from smcb_unlocker.job import RebootJob
from smcb_unlocker.sentry_checkins import SentryCheckins


PING_DELAY = timedelta(seconds=30)
PING_RETRY_INTERVAL = timedelta(seconds=10)
PING_RETRY_TIMEOUT = timedelta(minutes=10)


log = logging.getLogger(__name__)


class RebootWorker:
    credentials: ConfigCredentials
    sentry_checkins: SentryCheckins | None

    reboot_job_queue: asyncio.Queue[RebootJob] | None

    def __init__(
        self,
        credentials: ConfigCredentials,
        sentry_checkins: SentryCheckins | None = None,
    ):
        self.credentials = credentials
        self.sentry_checkins = sentry_checkins
        self.reboot_job_queue = None

    def connectInput(self, reboot_job_queue: asyncio.Queue[RebootJob]):
        self.reboot_job_queue = reboot_job_queue

    def ensure_connected(self):
        if not self.reboot_job_queue:
            raise RuntimeError("RebootWorker is not connected. Call 'connectInput' method first.")

    def get_credentials(self, konnektor_name: str) -> ConfigUserCredentials:
        return self.credentials.konnektors.get(konnektor_name, self.credentials.konnektors.get('_default'))

    async def handle(self, job: RebootJob):
        async with httpx.AsyncClient(verify=False) as client:
            creds = self.get_credentials(job.konnektor_name)
            auth = await login(client, job.konnektor_base_url, creds.username, creds.password)

            await reboot(client, job.konnektor_base_url, auth)
            log.info(f"Reboot triggered", extra={"job": job})

            log.info(f"Waiting {PING_DELAY.total_seconds()}s before pinging Konnektor", extra={"job": job})
            await asyncio.sleep(PING_DELAY.total_seconds())

            ping_start = datetime.now()
            now = ping_start

            while now - ping_start < PING_RETRY_TIMEOUT:
                if await ping(client, job.konnektor_base_url, auth):
                    log.info(f"Konnektor is back online", extra={"job": job})
                    return
            
                log.info(f"Konnektor is still offline, retrying in {PING_RETRY_INTERVAL.total_seconds()}s", extra={"job": job})

                await asyncio.sleep(PING_RETRY_INTERVAL.total_seconds())
                now = datetime.now()

            raise RuntimeError(f"Konnektor did not come back online within {PING_RETRY_TIMEOUT.total_seconds()}s")

    async def run(self):
        self.ensure_connected()
        while True:
            job = await self.reboot_job_queue.get()
            
            try:
                log.info(f"Start job", extra={"job": job})
                
                await self.handle(job)

                log.info(f"End job", extra={"job": job})
                if self.sentry_checkins:
                    self.sentry_checkins.ok(job)
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                log.warning("Konnektor unreachable: %s", e, extra={"job": job})
                if self.sentry_checkins:
                    self.sentry_checkins.error(job)
            except Exception as e:
                log.exception("Error during job", extra={"job": job})
                sentry_sdk.capture_exception(e)
                if self.sentry_checkins:
                    self.sentry_checkins.error(job)

            self.reboot_job_queue.task_done()
