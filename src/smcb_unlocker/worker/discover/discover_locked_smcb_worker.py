import asyncio
import logging

import httpx

from ..verify.smcb_verify_worker import SmcbVerifyWorker
from ...client.konnektor.admin import get_cards, get_mandants_for_card, get_pin_status_for_card, login
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
            
            cards = await get_cards(client, discover_job.konnektor_base_url, auth)
            smcb_cards = [card for card in cards if card.type == 'SMC_B']

            for smcb_card in smcb_cards:       
                mandants = await get_mandants_for_card(client, discover_job.konnektor_base_url, auth, smcb_card.cardhandle)
                if len(mandants) == 0:
                    log.warning(f"No mandants found for SMCB card with ICCSN {smcb_card.iccsn}")
                    continue
                mandant = mandants[0]

                pin_status = await get_pin_status_for_card(client, discover_job.konnektor_base_url, auth, smcb_card.cardhandle, mandant.mandant.mandantId)
                if pin_status.status == "VERIFIABLE":
                    verify_job = SmcbVerifyJob(
                        konnektor_base_url=discover_job.konnektor_base_url,
                        konnektor_admin_username=discover_job.konnektor_admin_username,
                        konnektor_admin_password=discover_job.konnektor_admin_password,
                        # TODO: Fetch KTs
                        kt_base_url="wss://10.0.22.111",
                        kt_mgmt_username=discover_job.kt_mgmt_username,
                        kt_mgmt_password=discover_job.kt_mgmt_password,
                        smcb_iccsn=smcb_card.iccsn,
                        smcb_pin=discover_job.smcb_pin,
                    )
                    await self.verify_job_queue.put(verify_job)

    async def run(self):
        self.ensure_connected()
        while True:
            discover_job = await self.discover_job_queue.get()
            await self.handle(discover_job)
            self.discover_job_queue.task_done()
