from typing import Literal
from pydantic import BaseModel
from smcb_unlocker.client.kt.mgmt.model.header import Header


class LogoutRequestPayload(BaseModel):
    pass


class LogoutRequest(BaseModel):
    header: Header
    payloadType: Literal["LogoutRequest"]
    payload: LogoutRequestPayload