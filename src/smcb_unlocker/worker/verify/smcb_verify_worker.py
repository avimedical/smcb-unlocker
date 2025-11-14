import asyncio
import logging

import sentry_sdk

from smcb_unlocker.worker.verify.konnektor_smcb_verifier import KonnektorSmcbVerifier
from smcb_unlocker.worker.verify.kt_smcb_verifier import KtSmcbVerifier
from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials, ConfigPinCredentials
from smcb_unlocker.job import SmcbVerifyJob


log = logging.getLogger(__name__)


class SmcbVerifyWorker:
    credentials: ConfigCredentials

    job_queue: asyncio.Queue[SmcbVerifyJob] | None

    def __init__(self, credentials: ConfigCredentials):
        self.credentials = credentials
        self.job_queue = None

    def connectInput(self, job_queue: asyncio.Queue[SmcbVerifyJob]):
        self.job_queue = job_queue

    def ensure_connected(self):
        if not self.job_queue:
            raise RuntimeError("SmcbVerifyWorker is not connected. Call 'connect' method on DiscoverLockedSmcbWorker first.")
        
    def get_kt_credentials(self, kt_mac: str) -> ConfigUserCredentials:
        return self.credentials.kt.get(kt_mac, self.credentials.kt['_default'])
    
    def get_smcb_credentials(self, smcb_iccsn: str) -> ConfigPinCredentials:
        return self.credentials.smcb.get(smcb_iccsn, self.credentials.smcb['_default'])

    async def handle(self, job: SmcbVerifyJob):
        kt_creds = self.get_kt_credentials(job.kt_mac)
        smcb_creds = self.get_smcb_credentials(job.smcb_iccsn)
        
        konnektor_ready = asyncio.Event()
        kt_ready = asyncio.Event()

        konnektor_verifier = KonnektorSmcbVerifier(
            base_url=job.konnektor_base_url,
            auth=job.konnektor_auth,
        )
        kt_verifier = KtSmcbVerifier(
            base_url=job.kt_base_url,
            mgmt_username=kt_creds.username,
            mgmt_password=kt_creds.password,
        )

        konnektor_verifier.connect(konnektor_ready, kt_ready)
        kt_verifier.connect(konnektor_ready, kt_ready)

        async with asyncio.TaskGroup() as tg:
            konnektor_task = tg.create_task(konnektor_verifier.run(job.smcb_cardhandle, job.mandant_id, job.kt_id))
            kt_task = tg.create_task(kt_verifier.run(smcb_creds.pin))

        return konnektor_task.result(), kt_task.result()

    async def run(self):
        self.ensure_connected()
        while True:
            job = await self.job_queue.get()

            try:
                log.info(f"START {job}")
                await self.handle(job)
                log.info(f"END {job}")
            except Exception as e:
                log.error(f"ERROR {job}: {e}")
                sentry_sdk.capture_exception(e)

            self.job_queue.task_done()
