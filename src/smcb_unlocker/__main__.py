import asyncio
import logging


from .config import Config
from .job import DiscoverLockedSmcbJob, SmcbVerifyJob
from .worker.discover.discover_locked_smcb_worker import DiscoverLockedSmcbWorker
from .worker.schedule.job_interval_scheduler import JobIntervalScheduler
from .worker.verify.smcb_verify_worker import SmcbVerifyWorker


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def main():
    config = Config()

    discover_job_queue: asyncio.Queue[DiscoverLockedSmcbJob] = asyncio.Queue()
    verify_job_queue: asyncio.Queue[SmcbVerifyJob] = asyncio.Queue()
    
    schedule_workers: list[JobIntervalScheduler[DiscoverLockedSmcbJob]] = [
        JobIntervalScheduler(lambda: DiscoverLockedSmcbJob(name, config.base_url), config.interval)
        for name, config in config.konnektors.items()
    ]
    discover_workers = [
        DiscoverLockedSmcbWorker(config.credentials)
        for _ in range(config.discover_workers)
    ]
    verify_workers = [
        SmcbVerifyWorker(config.credentials)
        for _ in range(config.verify_workers)
    ]

    for scheduler in schedule_workers:
        scheduler.connectOutput(discover_job_queue)
    for discover_worker in discover_workers:
        discover_worker.connectInput(discover_job_queue)
        discover_worker.connectOutput(verify_job_queue)
    for verify_worker in verify_workers:
        verify_worker.connectInput(verify_job_queue)

    async with asyncio.TaskGroup() as tg:
        for scheduler in schedule_workers:
            tg.create_task(scheduler.run())
        for discover_locked_smcb_worker in discover_workers:
            tg.create_task(discover_locked_smcb_worker.run())
        for smcb_verify_worker in verify_workers:
            tg.create_task(smcb_verify_worker.run())


if __name__ == "__main__":
    asyncio.run(main())
