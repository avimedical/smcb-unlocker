from abc import ABC, abstractmethod

from ..model import WsModel


class State(ABC):
    @abstractmethod
    async def handle_msg(self, msg: WsModel) -> None:
        pass
