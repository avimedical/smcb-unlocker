from pydantic import BaseModel


class MandantSmb(BaseModel):
    activationCode: str | None = None
    autoPin: bool
    autoPinVerificationEnabled: bool
    commonName: str | None = None
    hsm: bool
    iccsn: str
    telematikId: str | None = None


class MandantRemotePinCardTerminal(BaseModel):
    arbeitsplatzInternalId: str
    cardTerminalInternalId: str


class Mandant(BaseModel):
    assignedCardTerminalInternalIds: list[str]
    internalId: str
    managedSmbs: list[MandantSmb]
    mandantId: str
    # vHSKs respond with the list of strings, hardware Konnektors respond with the object
    remotePinCardTerminals: list[str] | list [MandantRemotePinCardTerminal]
    validateTelematikId: bool | None = None
