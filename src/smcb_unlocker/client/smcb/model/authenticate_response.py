from typing import Literal

from pydantic import BaseModel

from .header import Header


class AuthenticateResponsePayload(BaseModel):
    Response: str


class AuthenticateResponse(BaseModel):
    Header: Header
    PayloadType: Literal["AuthenticateResponse"]
    Payload: AuthenticateResponsePayload

