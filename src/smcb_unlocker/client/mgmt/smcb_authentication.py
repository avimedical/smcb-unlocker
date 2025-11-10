import logging
from typing import Literal

from pydantic import BaseModel
from websockets.asyncio.client import ClientConnection

from .shared import get_id, Header


log = logging.getLogger(__name__)


class SmcbAuthenticationRequestPayload(BaseModel):
    pass


class SmcbAuthenticationRequest(BaseModel):
    header: Header
    payloadType: Literal["SmcbAuthenticationRequest"]
    payload: SmcbAuthenticationRequestPayload


class SmcbAuthenticationResponsePayload(BaseModel):
    error: str | None = None
    key: str | None = None


class SmcbAuthenticationResponse(BaseModel):
    header: Header
    payloadType: Literal["SmcbAuthenticationResponse"]
    payload: SmcbAuthenticationResponsePayload


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
