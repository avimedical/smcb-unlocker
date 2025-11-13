import logging
from typing import Literal

from pydantic import BaseModel
from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.mgmt.shared import get_id, Header


log = logging.getLogger(__name__)


class LoginRequestPayload(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    header: Header
    payloadType: Literal["LoginRequest"]
    payload: LoginRequestPayload


class LoginResponsePayload(BaseModel):
    error: str | None = None
    sessionId: str | None = None


class LoginResponse(BaseModel):
    header: Header
    payloadType: Literal["LoginResponse"]
    payload: LoginResponsePayload


async def login(ws: ClientConnection, username: str, password: str) -> str:
    req = LoginRequest(
        header=Header(msgId=get_id()),
        payloadType="LoginRequest",
        payload=LoginRequestPayload(username=username, password=password)
    )
    req_json = req.model_dump_json(exclude_none=True)
    log.debug(f"REQ {req.header.msgId}: {req_json}")
    
    await ws.send(req_json)
    res_json = await ws.recv()

    res = LoginResponse.model_validate_json(res_json)
    log.debug(f"RES {res.header.msgId}: {res_json}")

    if res.payload.error is not None:
        raise RuntimeError(f"Login failed: {res.payload.error}")
    return res.payload.sessionId
