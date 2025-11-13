from collections.abc import Awaitable, Callable

from websockets.asyncio.client import ClientConnection

from smcb_unlocker.client.kt.smcb.model import WsModel
from smcb_unlocker.client.kt.smcb.states import State, StateContext, Connected, End


class StateMachine:
    ws: ClientConnection
    state: State | None
    ctx: StateContext


    def __init__(self, ws: ClientConnection, smcb_key: str, smcb_pin: str):
        self.ws = ws
        self.state = None
        self.ctx = StateContext(smcb_key=smcb_key, smcb_pin=smcb_pin)


    async def run(self):
        self.state = Connected(self.ws, self.ctx)
        yield self.state

        async for message in self.ws:
            ws_model_json = f'{{"msg": {message}}}'
            ws_model = WsModel.model_validate_json(ws_model_json)

            self.state = await self.state.handle_msg(ws_model)
            yield self.state

            if isinstance(self.state, End):
                break
