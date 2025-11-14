from pydantic import BaseModel


class MandantSmb(BaseModel):
    activationCode: str | None = None
    autoPin: bool
    autoPinVerificationEnabled: bool
    commonName: str | None = None
    hsm: bool
    iccsn: str
    telematikId: str | None = None


class Mandant(BaseModel):
    assignedCardTerminalInternalIds: list[str]
    internalId: str
    managedSmbs: list[MandantSmb]
    mandantId: str
    remotePinCardTerminals: list[str]
    validateTelematikId: bool | None = None
