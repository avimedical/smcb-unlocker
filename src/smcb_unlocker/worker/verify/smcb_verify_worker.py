import asyncio
import logging

from smcb_unlocker.worker.verify.konnektor_smcb_verifier import KonnektorSmcbVerifier
from smcb_unlocker.worker.verify.kt_smcb_verifier import KtSmcbVerifier
from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials, ConfigPinCredentials
from smcb_unlocker.job import SmcbVerifyJob
from smcb_unlocker.sentry_checkins import SentryCheckins
from smcb_unlocker.worker.base_worker import BaseWorker


log = logging.getLogger(__name__)


class SmcbVerifyWorker(BaseWorker[SmcbVerifyJob]):
    credentials: ConfigCredentials
    konnektor_verifier_factory: callable[[str, str], KonnektorSmcbVerifier]
    kt_verifier_factory: callable[[str, str, str], KtSmcbVerifier]

    def __init__(
            self,
            credentials: ConfigCredentials,
            konnektor_verifier_factory: callable[[str, str], KonnektorSmcbVerifier] = KonnektorSmcbVerifier.of,
            kt_verifier_factory: callable[[str, str, str], KtSmcbVerifier] = KtSmcbVerifier.of,
            sentry_checkins: SentryCheckins | None = None,
        ):
        super().__init__(sentry_checkins=sentry_checkins)
        self.credentials = credentials
        self.konnektor_verifier_factory = konnektor_verifier_factory
        self.kt_verifier_factory = kt_verifier_factory

    def connectInput(self, job_queue: asyncio.Queue[SmcbVerifyJob]):
        self.connect_job_queue(job_queue)

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
