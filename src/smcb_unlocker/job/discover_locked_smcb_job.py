from dataclasses import dataclass

@dataclass
class DiscoverLockedSmcbJob:
    konnektor_base_url: str
    konnektor_admin_username: str
    konnektor_admin_password: str
    kt_mgmt_username: str
    kt_mgmt_password: str
    smcb_pin: str
