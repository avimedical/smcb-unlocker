from typing import Literal

from pydantic import BaseModel

from smcb_unlocker.client.kt.smcb.model.header import Header


class AuthenticateRequestPayload(BaseModel):
    ApiVersion: str
    Challenge: str


class AuthenticateRequest(BaseModel):
    Header: Header
    PayloadType: Literal["AuthenticateRequest"]
    Payload: AuthenticateRequestPayload

