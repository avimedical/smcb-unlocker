import asyncio
import logging

import httpx

from ..verify.smcb_verify_worker import SmcbVerifyWorker
from ...client.konnektor.admin import get_card_terminals, get_mandants, get_pin_status_for_card, login
from ...job import DiscoverLockedSmcbJob, SmcbVerifyJob


log = logging.getLogger(__name__)


class DiscoverLockedSmcbWorker:
    discover_job_queue: asyncio.Queue[DiscoverLockedSmcbJob] | None
    verify_job_queue: asyncio.Queue[SmcbVerifyJob] | None

    def connectInput(self, disover_job_queue: asyncio.Queue[DiscoverLockedSmcbJob]):
        self.discover_job_queue = disover_job_queue

    def connectWorkers(self, workers: list[SmcbVerifyWorker]):
        self.verify_job_queue = asyncio.Queue()
        for worker in workers:
            worker.job_queue = self.verify_job_queue

    def ensure_connected(self):
        if not self.discover_job_queue or not self.verify_job_queue:
            raise RuntimeError("DiscoverLockedSmcbWorker is not connected. Call 'connect*' methods first.")

    async def handle(self, discover_job: DiscoverLockedSmcbJob):
        async with httpx.AsyncClient(verify=False) as client:
            auth = await login(client, discover_job.konnektor_base_url, discover_job.konnektor_admin_username, discover_job.konnektor_admin_password)
            
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
                            konnektor_base_url=discover_job.konnektor_base_url,
                            konnektor_auth=auth,
                            kt_id=card_terminal.cardTerminalId,
                            kt_base_url=f"wss://{card_terminal.ipAddress}",
                            kt_mgmt_username=discover_job.kt_mgmt_username,
                            kt_mgmt_password=discover_job.kt_mgmt_password,
                            smcb_iccsn=card.iccsn,
                            smcb_cardhandle=card.cardhandle,
                            smcb_pin=discover_job.smcb_pin,
                            mandant_id=mandant.mandantId,
                        )
                        await self.verify_job_queue.put(verify_job)  

    async def run(self):
        self.ensure_connected()
        while True:
            discover_job = await self.discover_job_queue.get()
            await self.handle(discover_job)
            self.discover_job_queue.task_done()
