import asyncio
import logging

from .config import Config
from .job import DiscoverLockedSmcbJob
from .worker.discover.discover_locked_smcb_worker import DiscoverLockedSmcbWorker
from .worker.verify.smcb_verify_worker import SmcbVerifyWorker


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def main():
    config = Config()

    discover_job_queue = asyncio.Queue()
    discover_locked_smcb_worker = DiscoverLockedSmcbWorker()
    smcb_verify_worker = SmcbVerifyWorker()
    discover_locked_smcb_worker.connectInput(discover_job_queue)
    discover_locked_smcb_worker.connectWorkers([smcb_verify_worker])

    async with asyncio.TaskGroup() as tg:
        tg.create_task(discover_locked_smcb_worker.run())
        tg.create_task(smcb_verify_worker.run())

        while True:
            job = DiscoverLockedSmcbJob(
                konnektor_base_url=config.konnektor_base_url,
                konnektor_admin_username=config.konnektor_admin_username,
                konnektor_admin_password=config.konnektor_admin_password,
                kt_mgmt_username=config.kt_mgmt_username,
                kt_mgmt_password=config.kt_mgmt_password,
                smcb_pin=config.smcb_pin,
            )
            await discover_job_queue.put(job)
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
