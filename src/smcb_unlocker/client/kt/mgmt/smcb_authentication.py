import logging

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.mgmt.model import SmcbAuthenticationRequest, SmcbAuthenticationRequestPayload, SmcbAuthenticationResponse, Header
from smcb_unlocker.client.kt.mgmt.util import get_id


log = logging.getLogger(__name__)


async def smcb_authentication(ws: ClientConnection, session_id: str) -> str:
    req = SmcbAuthenticationRequest(
        header=Header(msgId=get_id(), sessionId=session_id),
        payloadType="SmcbAuthenticationRequest",
        payload=SmcbAuthenticationRequestPayload()
    )
    req_json = req.model_dump_json(exclude_none=True)
    log.debug(f"REQ {req.header.msgId}: {req_json}")
    
    await ws.send(req_json)
    res_json = await ws.recv()

    res = SmcbAuthenticationResponse.model_validate_json(res_json)
    log.debug(f"RES {res.header.msgId}: {res_json}")

    if res.payload.error is not None:
        raise RuntimeError(f"SMCB Authentication failed: {res.payload.error}")
    return res.payload.key
