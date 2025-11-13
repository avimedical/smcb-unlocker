from typing import Literal

from pydantic import BaseModel

from smcb_unlocker.client.kt.smcb.model.header import Header

class NotifyPayload(BaseModel):
    Code: int

class Notify(BaseModel):
    Header: Header
    PayloadType: Literal["Notify"]
    Payload: NotifyPayload
