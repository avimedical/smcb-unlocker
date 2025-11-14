from typing import Literal

from pydantic import BaseModel

from smcb_unlocker.client.kt.mgmt.model.header import Header

class GetApiVersionResponsePayload(BaseModel):
    apiVersion: str


class GetApiVersionResponse(BaseModel):
    header: Header
    payloadType: Literal["GetApiVersionResponse"]
    payload: GetApiVersionResponsePayload
