from dataclasses import dataclass

@dataclass(frozen=True)
class DiscoverLockedSmcbJob:
    job_id: str
    konnektor_name: str
    konnektor_base_url: str
