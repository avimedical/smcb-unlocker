import asyncio
import logging

from .config import Config
from .job import SmcbVerifyJob
from .worker.verify.smcb_verify_worker import SmcbVerifyWorker


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def main():
    config = Config()

    smcb_verify_worker = SmcbVerifyWorker()
    job = SmcbVerifyJob(
        konnektor_base_url=config.konnektor_base_url,
        konnektor_admin_username=config.konnektor_admin_username,
        konnektor_admin_password=config.konnektor_admin_password,
        kt_base_url=config.kt_base_url,
        kt_mgmt_username=config.kt_mgmt_username,
        kt_mgmt_password=config.kt_mgmt_password,
        smcb_iccsn=config.smcb_iccsn,
        smcb_pin=config.smcb_pin,
    )
    await smcb_verify_worker.handle(job)


if __name__ == "__main__":
    asyncio.run(main())
