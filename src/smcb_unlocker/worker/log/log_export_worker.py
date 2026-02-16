import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging

import httpx

from smcb_unlocker.client.konnektor.admin import get_protocols, login
from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials
from smcb_unlocker.job import LogExportJob
from smcb_unlocker.sentry_checkins import SentryCheckins
from smcb_unlocker.worker.base_worker import BaseWorker


TO_DATETIME = datetime(2099, 12, 31, 00, 00, 00, tzinfo=timezone.utc)


log = logging.getLogger(__name__)


class LogExportWorker(BaseWorker[LogExportJob]):
    credentials: ConfigCredentials
    last_ts_map: dict[str, datetime]
    timeout: float

    def __init__(self, credentials: ConfigCredentials, timeout: float = 30.0, sentry_checkins: SentryCheckins | None = None):
        super().__init__(sentry_checkins=sentry_checkins)
        self.credentials = credentials
        self.timeout = timeout
        self.last_ts_map = defaultdict(lambda: datetime.now(timezone.utc))

    def connectInput(self, log_job_queue: asyncio.Queue[LogExportJob]):
        self.connect_job_queue(log_job_queue)

    def get_credentials(self, konnektor_name: str) -> ConfigUserCredentials:
        return self.credentials.konnektors.get(konnektor_name, self.credentials.konnektors.get('_default'))

    async def handle(self, job: LogExportJob):
        async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(self.timeout)) as client:
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
