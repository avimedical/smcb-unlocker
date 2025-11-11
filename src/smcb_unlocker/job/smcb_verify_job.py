from dataclasses import dataclass

@dataclass
class SmcbVerifyJob:
    konnektor_base_url: str
    konnektor_admin_username: str
    konnektor_admin_password: str
    kt_base_url: str
    kt_mgmt_username: str
    kt_mgmt_password: str
    smcb_iccsn: str
    smcb_pin: str
