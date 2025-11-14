from typing import Literal

from pydantic import BaseModel

from smcb_unlocker.client.kt.mgmt.model.header import Header


class GetApiVersionRequestPayload(BaseModel):
    pass


class GetApiVersionRequest(BaseModel):
    header: Header
    payloadType: Literal["GetApiVersionRequest"]
    payload: GetApiVersionRequestPayload
