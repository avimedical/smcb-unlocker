from pydantic import BaseModel, Field

from .authenticate_request import AuthenticateRequest
from .authenticate_response import AuthenticateResponse
from .notify import Notify


class WsModel(BaseModel):
    msg: AuthenticateRequest | AuthenticateResponse | Notify = Field(discriminator="PayloadType")
