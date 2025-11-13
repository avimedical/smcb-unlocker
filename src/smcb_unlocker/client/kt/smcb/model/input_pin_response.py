from typing import Literal

from pydantic import BaseModel

from smcb_unlocker.client.kt.smcb.model.header import Header


class InputPinResponsePayload(BaseModel):
    Code: str
    Pin: str


class InputPinResponse(BaseModel):
    Header: Header
    PayloadType: Literal["InputPinResponse"]
    Payload: InputPinResponsePayload
