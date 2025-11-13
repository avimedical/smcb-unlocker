import logging

from cryptography.hazmat.primitives import cmac
from cryptography.hazmat.primitives.ciphers import algorithms
from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.smcb.states.authenticated import Authenticated
from smcb_unlocker.client.kt.smcb.states.state import State
from smcb_unlocker.client.kt.smcb.states.state_context import StateContext
from smcb_unlocker.client.kt.smcb.states.util import get_id, NOTIFY_CODES
from smcb_unlocker.client.kt.smcb.model import AuthenticateRequest, AuthenticateResponse, AuthenticateResponsePayload, Header, Notify, WsModel


log = logging.getLogger(__name__)


class Connected(State):
    ws: ClientConnection
    ctx: StateContext

    def __init__(self, ws: ClientConnection, ctx: StateContext):
        self.ws = ws
        self.ctx = ctx

    def calculate_authenticate_response(self, challenge:str) -> str:
        key = self.ctx.smcb_key
        c = cmac.CMAC(algorithms.AES(bytes.fromhex(key)))
        c.update(bytes.fromhex(challenge))
        return c.finalize().hex()

    async def handle_authenticate_request(self, req: AuthenticateRequest) -> Connected:
        challenge = req.Payload.Challenge
        response_cmac = self.calculate_authenticate_response(challenge)

        res = AuthenticateResponse(
            Header=Header(MsgId=get_id(), InReplyToId=req.Header.MsgId),
            PayloadType="AuthenticateResponse",
            Payload=AuthenticateResponsePayload(Response=response_cmac)
        )
        res_json = res.model_dump_json(exclude_none=True)
        log.debug(f"RES {res.Header.MsgId}: {res_json}")
        await self.ws.send(res_json)

        return self
    
    async def handle_notify(self, notify: Notify) -> Authenticated:
        log.debug(f"NOTIFY {notify.Header.MsgId}: {notify.model_dump_json(exclude_none=True)}")

        if notify.Payload.Code != 0:
            raise RuntimeError(f"Notify error {notify.Payload.Code}: {NOTIFY_CODES.get(notify.Payload.Code, 'Unknown error code')}")

        return Authenticated(self.ws, self.ctx.with_session_id(notify.Header.SessionId))

    async def handle_msg(self, msg: WsModel) -> State:
        # Handle messages specific to the Connected state
        if isinstance(msg.msg, AuthenticateRequest):
            return await self.handle_authenticate_request(msg.msg)
        if isinstance(msg.msg, Notify):
            return await self.handle_notify(msg.msg)

        log.warning(f"Unhandled message type in Connected state: {type(msg.msg)}")
        return self
