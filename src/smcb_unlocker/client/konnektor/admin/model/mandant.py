from pydantic import BaseModel


class MandantSmb(BaseModel):
    activationCode: str | None
    autoPin: bool
    autoPinVerificationEnabled: bool
    commonName: str | None
    hsm: bool
    iccsn: str
    telematikId: str | None


class Mandant(BaseModel):
    assignedCardTerminalInternalIds: list[str]
    internalId: str
    managedSmbs: list[MandantSmb]
    mandantId: str
    remotePinCardTerminals: list[str]
    validateTelematikId: bool
