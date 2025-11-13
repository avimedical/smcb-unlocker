from dataclasses import dataclass

@dataclass
class SmcbVerifyJob:
    konnektor_base_url: str
    konnektor_auth: str
    kt_id: str
    kt_base_url: str
    kt_mac: str
    smcb_iccsn: str
    smcb_cardhandle: str
    mandant_id: str
