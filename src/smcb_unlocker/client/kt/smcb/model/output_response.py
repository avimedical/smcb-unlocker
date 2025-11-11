from typing import Literal

from pydantic import BaseModel

from .header import Header


class OutputResponsePayload(BaseModel):
    Code: str    


class OutputResponse(BaseModel):
    Header: Header
    PayloadType: Literal["OutputResponse"]
    Payload: OutputResponsePayload
