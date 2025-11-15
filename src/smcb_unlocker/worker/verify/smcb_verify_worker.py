import asyncio
import logging

from smcb_unlocker.worker.verify.konnektor_smcb_verifier import KonnektorSmcbVerifier
from smcb_unlocker.worker.verify.kt_smcb_verifier import KtSmcbVerifier
from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials, ConfigPinCredentials
from smcb_unlocker.job import SmcbVerifyJob
from smcb_unlocker.sentry_checkins import SentryCheckins


log = logging.getLogger(__name__)


class SmcbVerifyWorker:
    credentials: ConfigCredentials
    konnektor_verifier_factory: callable[[str, str], KonnektorSmcbVerifier]
    kt_verifier_factory: callable[[str, str, str], KtSmcbVerifier]
    sentry_checkins: SentryCheckins | None

    job_queue: asyncio.Queue[SmcbVerifyJob] | None

    def __init__(
            self,
            credentials: ConfigCredentials,
            konnektor_verifier_factory: callable[[str, str], KonnektorSmcbVerifier] = KonnektorSmcbVerifier.of,
            kt_verifier_factory: callable[[str, str, str], KtSmcbVerifier] = KtSmcbVerifier.of,
            sentry_checkins: SentryCheckins | None = None,
        ):
        self.credentials = credentials
        self.konnektor_verifier_factory = konnektor_verifier_factory
        self.kt_verifier_factory = kt_verifier_factory
        self.sentry_checkins = sentry_checkins
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

        konnektor_verifier = self.konnektor_verifier_factory(
            base_url=job.konnektor_base_url,
            auth=job.konnektor_auth,
        )
        kt_verifier = self.kt_verifier_factory(
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
                if self.sentry_checkins:
                    self.sentry_checkins.ok(job)
            except Exception as e:
                log.error(f"ERROR {job}: {e}")
                if self.sentry_checkins:
                    self.sentry_checkins.error(job, e)

            self.job_queue.task_done()
