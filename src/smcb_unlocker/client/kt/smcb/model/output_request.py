from typing import Literal

from pydantic import BaseModel

from .header import Header


class OutputRequestPayload(BaseModel):
    pass


class OutputRequest(BaseModel):
    Header: Header
    PayloadType: Literal["OutputRequest"]
    Payload: OutputRequestPayload
