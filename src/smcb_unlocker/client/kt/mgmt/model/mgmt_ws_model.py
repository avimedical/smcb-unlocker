from pydantic import BaseModel, Field

from smcb_unlocker.client.kt.mgmt.model.get_api_version_request import GetApiVersionRequest
from smcb_unlocker.client.kt.mgmt.model.get_api_version_response import GetApiVersionResponse
from smcb_unlocker.client.kt.mgmt.model.login_request import LoginRequest
from smcb_unlocker.client.kt.mgmt.model.login_response import LoginResponse
from smcb_unlocker.client.kt.mgmt.model.logout_request import LogoutRequest
from smcb_unlocker.client.kt.mgmt.model.logout_response import LogoutResponse
from smcb_unlocker.client.kt.mgmt.model.smcb_authentication_request import SmcbAuthenticationRequest
from smcb_unlocker.client.kt.mgmt.model.smcb_authentication_response import SmcbAuthenticationResponse

class WsModel(BaseModel):
    msg: GetApiVersionRequest | GetApiVersionResponse | LoginRequest | LoginResponse | LogoutRequest | LogoutResponse | SmcbAuthenticationRequest | SmcbAuthenticationResponse = Field(discriminator="payloadType")
