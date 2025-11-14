import logging

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.mgmt.model import LoginRequest, LoginRequestPayload, LoginResponse, Header
from smcb_unlocker.client.kt.mgmt.util import get_id


log = logging.getLogger(__name__)


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
