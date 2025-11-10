import logging
from typing import Literal

from pydantic import BaseModel
from websockets.asyncio.client import ClientConnection

from .shared import get_id, Header


log = logging.getLogger(__name__)


class GetApiVersionRequestPayload(BaseModel):
    pass


class GetApiVersionRequest(BaseModel):
    header: Header
    payloadType: Literal["GetApiVersionRequest"]
    payload: GetApiVersionRequestPayload


class GetApiVersionResponsePayload(BaseModel):
    apiVersion: str


class GetApiVersionResponse(BaseModel):
    header: Header
    payloadType: Literal["GetApiVersionResponse"]
    payload: GetApiVersionResponsePayload


async def get_api_version(ws: ClientConnection) -> str:
    req = GetApiVersionRequest(header=Header(msgId=get_id()), payloadType="GetApiVersionRequest", payload=GetApiVersionRequestPayload())
    req_json = req.model_dump_json(exclude_none=True)
    log.debug(f"REQ {req.header.msgId}: {req_json}")
    
    await ws.send(req_json)
    res_json = await ws.recv()

    res = GetApiVersionResponse.model_validate_json(res_json)
    log.debug(f"RES {res.header.msgId}: {res_json}")
    return res.payload.apiVersion
