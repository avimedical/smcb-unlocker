from collections.abc import Awaitable, Callable

from websockets.asyncio.client import ClientConnection

from .model import WsModel
from .states import State, StateContext, Authenticated, Connected


class StateMachine:
    ws: ClientConnection
    state: State | None
    ctx: StateContext
    on_state_change: Callable[[State, State], Awaitable[None]] | None = None


    def __init__(self, ws: ClientConnection, smcb_key: str, smcb_pin: str, on_state_change: Callable[[State, State], Awaitable[None]] | None = None):
        self.ws = ws
        self.state = None
        self.ctx = StateContext(smcb_key=smcb_key, smcb_pin=smcb_pin)
        self.on_state_change = on_state_change


    async def run(self):
        self.state = Connected(self.ws, self.ctx)

        async for message in self.ws:
            ws_model_json = f'{{"msg": {message}}}'
            ws_model = WsModel.model_validate_json(ws_model_json)
            
            new_state = await self.state.handle_msg(ws_model)
            if new_state is not self.state and self.on_state_change:
                await self.on_state_change(self.state, new_state)
            self.state = new_state
