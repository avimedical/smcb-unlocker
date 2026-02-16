import asyncio
import logging
import uuid

import httpx

from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials
from smcb_unlocker.client.konnektor.admin import get_card_terminals, get_mandants, get_pin_status_for_card, login
from smcb_unlocker.job import DiscoverLockedSmcbJob, SmcbVerifyJob
from smcb_unlocker.sentry_checkins import SentryCheckins
from smcb_unlocker.worker.base_worker import BaseWorker


log = logging.getLogger(__name__)


class DiscoverLockedSmcbWorker(BaseWorker[DiscoverLockedSmcbJob]):
    credentials: ConfigCredentials
    verify_job_queue: asyncio.Queue[SmcbVerifyJob] | None
    timeout: float

    def __init__(self, credentials: ConfigCredentials, timeout: float = 30.0, sentry_checkins: SentryCheckins | None = None):
        super().__init__(sentry_checkins=sentry_checkins)
        self.credentials = credentials
        self.timeout = timeout
        self.verify_job_queue = None

    def connectInput(self, discover_job_queue: asyncio.Queue[DiscoverLockedSmcbJob]):
        self.connect_job_queue(discover_job_queue)

    def connectOutput(self, verify_job_queue: asyncio.Queue[SmcbVerifyJob]):
        self.verify_job_queue = verify_job_queue

    async def run(self):
        if not self.verify_job_queue:
            raise RuntimeError("DiscoverLockedSmcbWorker is not connected. Call 'connectOutput' first.")
        await super().run()

    def get_credentials(self, konnektor_name: str) -> ConfigUserCredentials:
        return self.credentials.konnektors.get(konnektor_name, self.credentials.konnektors.get('_default'))

    async def handle(self, discover_job: DiscoverLockedSmcbJob):
        async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(self.timeout)) as client:
            creds = self.get_credentials(discover_job.konnektor_name)
            auth = await login(client, discover_job.konnektor_base_url, creds.username, creds.password)

            mandants = await get_mandants(client, discover_job.konnektor_base_url, auth)
            card_terminals = await get_card_terminals(client, discover_job.konnektor_base_url, auth)

            mandants_by_smcb_iccsn = { smb.iccsn: mandant for mandant in mandants for smb in mandant.managedSmbs }

            for card_terminal in card_terminals:
                for card in card_terminal.slotInfos:
                    if card.type != 'SMC_B':
                        continue

                    mandant = mandants_by_smcb_iccsn.get(card.iccsn)
                    if not mandant:
                        log.warning(f"No mandant found for SMCB card with ICCSN {card.iccsn}")
                        continue

                    pin_status = await get_pin_status_for_card(client, discover_job.konnektor_base_url, auth, card.cardhandle, mandant.mandantId)
                    if pin_status.status == "VERIFIABLE":
                        verify_job = SmcbVerifyJob(
                            job_id=str(uuid.uuid4()),
                            konnektor_name=discover_job.konnektor_name,
                            konnektor_base_url=discover_job.konnektor_base_url,
                            konnektor_auth=auth,
                            kt_id=card_terminal.cardTerminalId,
                            kt_base_url=f"wss://{card_terminal.ipAddress}",
                            kt_mac=card_terminal.macAddress,
                            smcb_iccsn=card.iccsn,
                            smcb_cardhandle=card.cardhandle,
                            mandant_id=mandant.mandantId,
                        )
                        if self.sentry_checkins:
                            self.sentry_checkins.in_progress(verify_job)

                        await self.verify_job_queue.put(verify_job)
