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
    discover_locked_smcb_worker = DiscoverLockedSmcbWorker(config.credentials)
    smcb_verify_worker = SmcbVerifyWorker(config.credentials)
    discover_locked_smcb_worker.connectInput(discover_job_queue)
    discover_locked_smcb_worker.connectWorkers([smcb_verify_worker])

    async with asyncio.TaskGroup() as tg:
        tg.create_task(discover_locked_smcb_worker.run())
        tg.create_task(smcb_verify_worker.run())

        konnektor_config = config.konnektors['dev']
        while True:
            job = DiscoverLockedSmcbJob(
                konnektor_name='dev',
                konnektor_base_url=konnektor_config.base_url,
            )
            await discover_job_queue.put(job)
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
