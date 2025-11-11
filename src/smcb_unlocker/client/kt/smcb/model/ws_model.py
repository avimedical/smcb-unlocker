from pydantic import BaseModel, Field

from .authenticate_request import AuthenticateRequest
from .authenticate_response import AuthenticateResponse
from .input_pin_request import InputPinRequest
from .input_pin_response import InputPinResponse
from .notify import Notify
from .output_request import OutputRequest
from .output_response import OutputResponse


class WsModel(BaseModel):
    msg: AuthenticateRequest | AuthenticateResponse | InputPinRequest | InputPinResponse | Notify | OutputRequest | OutputResponse = Field(discriminator="PayloadType")
