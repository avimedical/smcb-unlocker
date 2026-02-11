import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging

import httpx
import sentry_sdk

from smcb_unlocker.client.konnektor.admin import get_protocols, login
from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials
from smcb_unlocker.job import LogExportJob
from smcb_unlocker.sentry_checkins import SentryCheckins


TO_DATETIME = datetime(2099, 12, 31, 00, 00, 00, tzinfo=timezone.utc)


log = logging.getLogger(__name__)


class LogExportWorker:
    credentials: ConfigCredentials
    sentry_checkins: SentryCheckins | None

    log_job_queue: asyncio.Queue[LogExportJob] | None
    last_ts_map: dict[str, datetime]

    def __init__(self, credentials: ConfigCredentials, sentry_checkins: SentryCheckins | None = None):
        self.credentials = credentials
        self.sentry_checkins = sentry_checkins
        self.log_job_queue = None
        self.last_ts_map = defaultdict(lambda: datetime.now(timezone.utc))

    def connectInput(self, log_job_queue: asyncio.Queue[LogExportJob]):
        self.log_job_queue = log_job_queue

    def ensure_connected(self):
        if not self.log_job_queue:
            raise RuntimeError("LogExportWorker is not connected. Call 'connectInput' method first.")

    def get_credentials(self, konnektor_name: str) -> ConfigUserCredentials:
        return self.credentials.konnektors.get(konnektor_name, self.credentials.konnektors.get('_default'))

    async def handle(self, job: LogExportJob):
        async with httpx.AsyncClient(verify=False) as client:
            creds = self.get_credentials(job.konnektor_name)
            auth = await login(client, job.konnektor_base_url, creds.username, creds.password)

            from_datetime = self.last_ts_map[job.konnektor_name]
            protocols = await get_protocols(client, job.konnektor_base_url, auth, from_datetime, TO_DATETIME)

            for protocol in protocols:
                protocol_severity = logging.getLevelNamesMapping()[protocol.severity]
                protocol_dt = datetime.fromtimestamp(float(protocol.timestampAsDateTime), timezone.utc)
                
                log.log(protocol_severity, protocol.message, extra={ "job": job, "protocol": protocol })

                if protocol_dt > self.last_ts_map[job.konnektor_name]:
                    # Round up to the next second because the Konnektor protocol entries have millisecond precision,
                    # but the query parameters in the API only have second precision. Without this, we could end up
                    # flooring the timestamp with int() and re-fetching the same entries again.
                    self.last_ts_map[job.konnektor_name] = (protocol_dt + timedelta(seconds=1)).replace(microsecond=0)

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
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                log.warning("Konnektor unreachable: %s", e, extra={"job": job})
                if self.sentry_checkins:
                    self.sentry_checkins.error(job)
            except Exception as e:
                log.exception("Error during job", extra={"job": job})
                sentry_sdk.capture_exception(e)
                if self.sentry_checkins:
                    self.sentry_checkins.error(job)

            self.log_job_queue.task_done()
