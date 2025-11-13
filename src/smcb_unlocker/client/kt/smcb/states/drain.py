import logging

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.smcb.states.end import End
from smcb_unlocker.client.kt.smcb.states.state import State
from smcb_unlocker.client.kt.smcb.states.state_context import StateContext
from smcb_unlocker.client.kt.smcb.model import OutputRequest, WsModel


log = logging.getLogger(__name__)


class Drain(State):
    ws: ClientConnection
    ctx: StateContext

    def __init__(self, ws: ClientConnection, ctx: StateContext):
        self.ws = ws
        self.ctx = ctx


    async def handle_output_request(self, req: OutputRequest) -> End:
        log.debug(f"OUTPUT REQUEST {req.Header.MsgId}: {req.model_dump_json(exclude_none=True)}")
        return End(self.ws, self.ctx)


    async def handle_msg(self, msg: WsModel) -> State:
        # Handle messages specific to the drain state
        if isinstance(msg.msg, OutputRequest):
            return await self.handle_output_request(msg.msg)

        log.warning(f"Unhandled message type in Drain state: {type(msg.msg)}")
        return self
