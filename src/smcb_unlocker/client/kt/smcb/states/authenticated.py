import logging

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.smcb.states.drain import Drain
from smcb_unlocker.client.kt.smcb.states.state import State
from smcb_unlocker.client.kt.smcb.states.state_context import StateContext
from smcb_unlocker.client.kt.smcb.states.util import get_id, NOTIFY_CODES
from smcb_unlocker.client.kt.smcb.model import Header, InputPinRequest, InputPinResponse, InputPinResponsePayload, Notify, WsModel


log = logging.getLogger(__name__)


class Authenticated(State):
    ws: ClientConnection
    ctx: StateContext

    def __init__(self, ws: ClientConnection, ctx: StateContext):
        self.ws = ws
        self.ctx = ctx

    async def handle_input_pin_request(self, req: InputPinRequest) -> Authenticated:
        res = InputPinResponse(
            Header=Header(MsgId=get_id(), InReplyToId=req.Header.MsgId, SessionId=self.ctx.session_id),
            PayloadType="InputPinResponse",
            Payload=InputPinResponsePayload(Code="Pin", Pin=self.ctx.smcb_pin)
        )
        res_json = res.model_dump_json(exclude_none=True)
        log.debug(f"RES {res.Header.MsgId}: {res_json}")
        await self.ws.send(res_json)

        return self
    

    async def handle_notify(self, notify: Notify) -> Authenticated:
        log.debug(f"NOTIFY {notify.Header.MsgId}: {notify.model_dump_json(exclude_none=True)}")

        if notify.Payload.Code != 0:
            raise RuntimeError(f"Notify error {notify.Payload.Code}: {NOTIFY_CODES.get(notify.Payload.Code, 'Unknown error code')}")

        return Drain(self.ws, self.ctx)


    async def handle_msg(self, msg: WsModel) -> State:
        # Handle messages specific to the authenticated state
        if isinstance(msg.msg, InputPinRequest):
            return await self.handle_input_pin_request(msg.msg)
        if isinstance(msg.msg, Notify):
            return await self.handle_notify(msg.msg)

        log.warning(f"Unhandled message type in Authenticated state: {type(msg.msg)}")
        return self
