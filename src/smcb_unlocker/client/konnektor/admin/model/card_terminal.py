from pydantic import BaseModel

from smcb_unlocker.client.konnektor.admin.model.card import Card


class CardTerminalProductinformation(BaseModel):
    ehealthInterfaceVersion: str | None = None
    firmwareGroupVersion: str | None = None
    firmwareVersion: str | None = None
    hardwareVersion: str | None = None
    informationDate: int | None = None
    manufacturer: str | None = None
    model: str | None = None
    productTypeVersion: str | None = None
    sicctVersion: str | None = None
    softwareVersion: str | None = None


class CardTerminalProtocolErrorLifetime(BaseModel):
    amount: int
    unit: str


class CardTerminal(BaseModel):
    adminPassword: str | None
    adminUsername: str | None
    authCertificate: str | None = None
    autoUpdate: bool
    cardStatusSwallowedCheckEnabled: bool
    cardTerminalId: str
    connected: bool
    correlation: str
    expirationAuthCertificate: int | None = None
    hostname: str
    internalId: str
    ipAddress: str
    label: str
    macAddress: str
    pairingConnectorSubjectName: str | None = None
    physical: bool
    port: int
    productinformation: CardTerminalProductinformation
    protocolErrorLifetime: CardTerminalProtocolErrorLifetime | None = None
    protocolErrorMax: int | None = None
    renewPairingNeeded: bool | None = None
    slotCount: int
    slotInfos: list[Card]
    userRole: str | None = None
    validSicctVersion: bool | None = None
