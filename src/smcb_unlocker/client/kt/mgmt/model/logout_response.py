from typing import Literal
from pydantic import BaseModel
from smcb_unlocker.client.kt.mgmt.model.header import Header


class LogoutResponsePayload(BaseModel):
    pass


class LogoutResponse(BaseModel):
    header: Header
    payloadType: Literal["LogoutResponse"]
    payload: LogoutResponsePayload