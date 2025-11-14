import logging

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.mgmt.model import LogoutRequest, LogoutRequestPayload, LogoutResponse, Header
from smcb_unlocker.client.kt.mgmt.util import get_id


log = logging.getLogger(__name__)


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
