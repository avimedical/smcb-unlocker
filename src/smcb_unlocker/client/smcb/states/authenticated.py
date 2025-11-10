from websockets.asyncio.client import ClientConnection

from .state import State
from .state_context import StateContext
from ..model import WsModel

class Authenticated(State):
    ws: ClientConnection
    ctx: StateContext

    def __init__(self, ws: ClientConnection, ctx: StateContext):
        self.ws = ws
        self.ctx = ctx

    async def handle_msg(self, msg: WsModel) -> State:
        # Handle messages specific to the authenticated state
        pass
