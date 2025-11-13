import logging

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.smcb.states.state import State
from smcb_unlocker.client.kt.smcb.states.state_context import StateContext
from smcb_unlocker.client.kt.smcb.model import WsModel


log = logging.getLogger(__name__)


class End(State):
    ws: ClientConnection
    ctx: StateContext

    def __init__(self, ws: ClientConnection, ctx: StateContext):
        self.ws = ws
        self.ctx = ctx

    async def handle_msg(self, msg: WsModel) -> State:
        # End state should not handle any messages
        log.warning(f"Unhandled message type in End state: {type(msg.msg)}")
        return self
