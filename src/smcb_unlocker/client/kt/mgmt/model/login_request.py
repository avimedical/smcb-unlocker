from typing import Literal
from pydantic import BaseModel
from smcb_unlocker.client.kt.mgmt.model.header import Header


class LoginRequestPayload(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    header: Header
    payloadType: Literal["LoginRequest"]
    payload: LoginRequestPayload