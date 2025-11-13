from pydantic import BaseModel, Field

from smcb_unlocker.client.kt.smcb.model.authenticate_request import AuthenticateRequest
from smcb_unlocker.client.kt.smcb.model.authenticate_response import AuthenticateResponse
from smcb_unlocker.client.kt.smcb.model.input_pin_request import InputPinRequest
from smcb_unlocker.client.kt.smcb.model.input_pin_response import InputPinResponse
from smcb_unlocker.client.kt.smcb.model.notify import Notify
from smcb_unlocker.client.kt.smcb.model.output_request import OutputRequest
from smcb_unlocker.client.kt.smcb.model.output_response import OutputResponse


class WsModel(BaseModel):
    msg: AuthenticateRequest | AuthenticateResponse | InputPinRequest | InputPinResponse | Notify | OutputRequest | OutputResponse = Field(discriminator="PayloadType")
