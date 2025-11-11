import asyncio

from .konnektor_smcb_verifier import KonnektorSmcbVerifier
from .kt_smcb_verifier import KtSmcbVerifier
from ...job import SmcbVerifyJob


class SmcbVerifyWorker:
    job_queue: asyncio.Queue[SmcbVerifyJob] | None

    def ensure_connected(self):
        if not self.job_queue:
            raise RuntimeError("SmcbVerifyWorker is not connected. Call 'connect' method on DiscoverLockedSmcbWorker first.")

    async def handle(self, job: SmcbVerifyJob):
        konnektor_verifier = KonnektorSmcbVerifier(
            base_url=job.konnektor_base_url,
            admin_username=job.konnektor_admin_username,
            admin_password=job.konnektor_admin_password,
        )
        kt_verifier = KtSmcbVerifier(
            base_url=job.kt_base_url,
            mgmt_username=job.kt_mgmt_username,
            mgmt_password=job.kt_mgmt_password,
        )
        konnektor_verifier.connect(kt_verifier)

        async with asyncio.TaskGroup() as tg:
            konnektor_task = tg.create_task(konnektor_verifier.run(job.smcb_iccsn))
            kt_task = tg.create_task(kt_verifier.run(job.smcb_pin))

        return konnektor_task.result(), kt_task.result()
    
    async def run(self):
        self.ensure_connected()
        while True:
            job = await self.job_queue.get()
            await self.handle(job)
            self.job_queue.task_done()
