from pydantic import BaseModel


from .card import Card


class CardTerminalProductinformation(BaseModel):
    ehealthInterfaceVersion: str
    firmwareGroupVersion: str
    firmwareVersion: str
    hardwareVersion: str
    informationDate: int
    manufacturer: str
    model: str
    productTypeVersion: str
    sicctVersion: str
    softwareVersion: str


class CardTerminalProtocolErrorLifetime(BaseModel):
    amount: int
    unit: str


class CardTerminal(BaseModel):
    adminPassword: str | None
    adminUsername: str | None
    authCertificate: str
    autoUpdate: bool
    cardStatusSwallowedCheckEnabled: bool
    cardTerminalId: str
    connected: bool
    correlation: str
    expirationAuthCertificate: int
    hostname: str
    internalId: str
    ipAddress: str
    label: str
    macAddress: str
    pairingConnectorSubjectName: str
    physical: bool
    port: int
    productinformation: CardTerminalProductinformation
    protocolErrorLifetime: CardTerminalProtocolErrorLifetime
    protocolErrorMax: int
    renewPairingNeeded: bool
    slotCount: int
    slotInfos: list[Card]
    userRole: str
    validSicctVersion: bool
