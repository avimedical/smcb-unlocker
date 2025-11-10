from typing import Literal

from pydantic import BaseModel

from .header import Header

class NotifyPayload(BaseModel):
    Code: int

class Notify(BaseModel):
    Header: Header
    PayloadType: Literal["Notify"]
    Payload: NotifyPayload
