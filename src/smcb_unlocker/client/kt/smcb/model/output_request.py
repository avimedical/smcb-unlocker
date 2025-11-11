from typing import Literal

from pydantic import BaseModel

from .header import Header


class OutputRequestPayload(BaseModel):
    Slot: str | None = None
    Atr: str | None = None
    Message: str
    MessageType: str
    MessageCode: str
    Timeout: int
    OkButton: bool
    CancelButton: bool
    ExpectResponse: bool


class OutputRequest(BaseModel):
    Header: Header
    PayloadType: Literal["OutputRequest"]
    Payload: OutputRequestPayload
