from dataclasses import dataclass

@dataclass
class SmcbVerifyJob:
    konnektor_base_url: str
    konnektor_auth: str
    kt_id: str
    kt_base_url: str
    kt_mgmt_username: str
    kt_mgmt_password: str
    smcb_iccsn: str
    smcb_cardhandle: str
    smcb_pin: str
    mandant_id: str
