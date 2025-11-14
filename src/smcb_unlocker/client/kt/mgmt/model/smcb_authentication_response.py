from typing import Literal
from pydantic import BaseModel
from smcb_unlocker.client.kt.mgmt.model.header import Header


class SmcbAuthenticationResponsePayload(BaseModel):
    error: str | None = None
    key: str | None = None


class SmcbAuthenticationResponse(BaseModel):
    header: Header
    payloadType: Literal["SmcbAuthenticationResponse"]
    payload: SmcbAuthenticationResponsePayload