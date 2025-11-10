from typing import Literal

from pydantic import BaseModel

from .header import Header


class AuthenticateRequestPayload(BaseModel):
    ApiVersion: str
    Challenge: str


class AuthenticateRequest(BaseModel):
    Header: Header
    PayloadType: Literal["AuthenticateRequest"]
    Payload: AuthenticateRequestPayload

