from typing import Literal
from pydantic import BaseModel
from smcb_unlocker.client.kt.mgmt.model.header import Header


class LoginResponsePayload(BaseModel):
    error: str | None = None
    sessionId: str | None = None


class LoginResponse(BaseModel):
    header: Header
    payloadType: Literal["LoginResponse"]
    payload: LoginResponsePayload