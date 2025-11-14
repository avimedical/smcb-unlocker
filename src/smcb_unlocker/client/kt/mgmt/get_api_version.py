import logging

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.mgmt.model import GetApiVersionRequest, GetApiVersionRequestPayload, GetApiVersionResponse, Header
from smcb_unlocker.client.kt.mgmt.util import get_id


log = logging.getLogger(__name__)


async def get_api_version(ws: ClientConnection) -> str:
    req = GetApiVersionRequest(header=Header(msgId=get_id()), payloadType="GetApiVersionRequest", payload=GetApiVersionRequestPayload())
    req_json = req.model_dump_json(exclude_none=True)
    log.debug(f"REQ {req.header.msgId}: {req_json}")
    
    await ws.send(req_json)
    res_json = await ws.recv()

    res = GetApiVersionResponse.model_validate_json(res_json)
    log.debug(f"RES {res.header.msgId}: {res_json}")
    return res.payload.apiVersion
