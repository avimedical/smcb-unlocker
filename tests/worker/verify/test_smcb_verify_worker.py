import asyncio

from pytest_mock import MockerFixture

from smcb_unlocker.config import ConfigCredentials, ConfigUserCredentials, ConfigPinCredentials
from smcb_unlocker.worker.verify.konnektor_smcb_verifier import KonnektorSmcbVerifier
from smcb_unlocker.worker.verify.kt_smcb_verifier import KtSmcbVerifier
from smcb_unlocker.worker.verify.smcb_verify_worker import SmcbVerifyWorker
from smcb_unlocker.job import SmcbVerifyJob 


async def test_smcb_verify_worker_runs(mocker: MockerFixture):
    verify_queue = asyncio.Queue()

    konnektor_creds = ConfigUserCredentials(username="testuser", password="testpass")
    kt_creds = ConfigUserCredentials(username="ktuser", password="ktpass")
    smcb_creds = ConfigPinCredentials(pin="123456")
    credentials = ConfigCredentials(konnektors={"_default": konnektor_creds}, kt={"_default": kt_creds}, smcb={"_default": smcb_creds})

    konnektor_verifier_mock = mocker.MagicMock(spec=KonnektorSmcbVerifier)
    kt_verifier_mock = mocker.MagicMock(spec=KtSmcbVerifier)

    worker = SmcbVerifyWorker(
        credentials=credentials,
        konnektor_verifier_factory=lambda base_url, auth: konnektor_verifier_mock,
        kt_verifier_factory=lambda base_url, mgmt_username, mgmt_password: kt_verifier_mock,
    )

    worker.connectInput(verify_queue)

    async with asyncio.TaskGroup() as tg:
        task = tg.create_task(worker.run())

        job = SmcbVerifyJob(
            konnektor_base_url="https://konnektor.test",
            konnektor_auth="Bearer testtoken",
            kt_id="KT-1",
            kt_base_url="wss://kt.test",
            kt_mac="00:11:22:33:44:55",
            smcb_iccsn="8901234567890123456",
            smcb_cardhandle="SMC-B-1",
            mandant_id="MANDANT-1"
        )
        await verify_queue.put(job)
        # Wait for the queue to be processed
        await verify_queue.join()

        konnektor_verifier_mock.run.assert_called_with("SMC-B-1", "MANDANT-1", "KT-1")
        kt_verifier_mock.run.assert_called_with("123456")

        task.cancel()
