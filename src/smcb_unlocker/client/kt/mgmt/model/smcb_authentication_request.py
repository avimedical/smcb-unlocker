from typing import Literal
from pydantic import BaseModel
from smcb_unlocker.client.kt.mgmt.model.header import Header


class SmcbAuthenticationRequestPayload(BaseModel):
    pass


class SmcbAuthenticationRequest(BaseModel):
    header: Header
    payloadType: Literal["SmcbAuthenticationRequest"]
    payload: SmcbAuthenticationRequestPayload