from typing import Literal

from pydantic import BaseModel

from .header import Header


class InputPinRequestPayload(BaseModel):
    Slot: str
    Atr: str
    Prompt: str
    Message: str
    MessageType: str
    MinLen: int
    MaxLen: int
    TimeoutFirst: int
    TimeoutOther: int
    TimeoutAll: int
    OkButton: bool
    CancelButton: bool


class InputPinRequest(BaseModel):
    Header: Header
    PayloadType: Literal["InputPinRequest"]
    Payload: InputPinRequestPayload
