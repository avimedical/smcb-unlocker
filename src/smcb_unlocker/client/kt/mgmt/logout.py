import logging
from typing import Literal

from pydantic import BaseModel
from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.mgmt.shared import get_id, Header


log = logging.getLogger(__name__)


class LogoutRequestPayload(BaseModel):
    pass


class LogoutRequest(BaseModel):
    header: Header
    payloadType: Literal["LogoutRequest"]
    payload: LogoutRequestPayload


class LogoutResponsePayload(BaseModel):
    pass


class LogoutResponse(BaseModel):
    header: Header
    payloadType: Literal["LogoutResponse"]
    payload: LogoutResponsePayload


async def logout(ws: ClientConnection, session_id: str) -> None:
    req = LogoutRequest(
        header=Header(msgId=get_id(), sessionId=session_id),
        payloadType="LogoutRequest",
        payload=LogoutRequestPayload()
    )
    req_json = req.model_dump_json(exclude_none=True)
    log.debug(f"REQ {req.header.msgId}: {req_json}")
    
    await ws.send(req_json)
    res_json = await ws.recv()

    res = LogoutResponse.model_validate_json(res_json)
    log.debug(f"RES {res.header.msgId}: {res_json}")
