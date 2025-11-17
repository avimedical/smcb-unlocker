
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

from sentry_sdk import capture_exception
from sentry_sdk.crons import capture_checkin
from sentry_sdk.crons.consts import MonitorStatus

from smcb_unlocker.job import DiscoverLockedSmcbJob, LogExportJob, SmcbVerifyJob


ORPHANED_CHECKIN_TIMEOUT = timedelta(minutes=30)
ORPHANED_CHECKIN_CLEANUP_INTERVAL = timedelta(minutes=10)


@dataclass(frozen=True)
class SentryCheckinKey:
    monitor_slug: str
    job_id: str


@dataclass(frozen=True)
class SentryCheckinValue:
    started_at: datetime
    check_in_id: str


class SentryCheckins:
    monitor_slug_prefix: str
    checkins: dict[SentryCheckinKey, SentryCheckinValue]
    
    def __init__(self, monitor_slug_prefix: str):
        self.monitor_slug_prefix = monitor_slug_prefix
        self.checkins = {}

    def get_monitor_slug(self, job: DiscoverLockedSmcbJob | LogExportJob | SmcbVerifyJob) -> str:
        if isinstance(job, DiscoverLockedSmcbJob):
            return f"{self.monitor_slug_prefix}-discover-{job.konnektor_name}"
        elif isinstance(job, LogExportJob):
            return f"{self.monitor_slug_prefix}-log-{job.konnektor_name}"
        elif isinstance(job, SmcbVerifyJob):
            return f"{self.monitor_slug_prefix}-verify-{job.konnektor_name}"
        else:
            raise ValueError("Unsupported job type for SentryCheckins")

    def in_progress(self, job: DiscoverLockedSmcbJob | LogExportJob | SmcbVerifyJob):
        monitor_slug = self.get_monitor_slug(job)
        check_in_id = capture_checkin(monitor_slug, status=MonitorStatus.IN_PROGRESS)
        
        key = SentryCheckinKey(monitor_slug, job.job_id)
        value = SentryCheckinValue(datetime.now(), check_in_id)
        self.checkins[key] = value

    def ok(self, job: DiscoverLockedSmcbJob | LogExportJob | SmcbVerifyJob):
        monitor_slug = self.get_monitor_slug(job)
        key = SentryCheckinKey(monitor_slug, job.job_id)
        value = self.checkins.pop(key, None)
        if not value:
            return
        
        capture_checkin(
            monitor_slug,
            check_in_id=value.check_in_id,
            status=MonitorStatus.OK,
            duration=(datetime.now() - value.started_at).total_seconds(),
        )

    def error(self, job: DiscoverLockedSmcbJob | LogExportJob | SmcbVerifyJob):
        monitor_slug = self.get_monitor_slug(job)
        key = SentryCheckinKey(monitor_slug, job.job_id)
        value = self.checkins.pop(key, None)
        if not value:
            return

        capture_checkin(
            monitor_slug,
            check_in_id=value.check_in_id,
            status=MonitorStatus.ERROR,
            duration=(datetime.now() - value.started_at).total_seconds(),
        )

    async def cleanup_orphaned_checkins(self):
        while True:
            now = datetime.now()
            orphaned_keys = [
                key for key, value in self.checkins.items()
                if now - value.started_at > ORPHANED_CHECKIN_TIMEOUT
            ]
            for key in orphaned_keys:
                del self.checkins[key]
            
            await asyncio.sleep(ORPHANED_CHECKIN_CLEANUP_INTERVAL.total_seconds())
