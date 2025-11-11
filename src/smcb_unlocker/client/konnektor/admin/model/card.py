from pydantic import BaseModel


class CardVersion(BaseModel):
    atr: str
    cos: str
    dataStructure: str | None
    gdo: str
    keyInfo: str | None
    logging: str | None
    objectSystem: str
    ptPers: str | None


class Card(BaseModel):
    cardTerminalHostname: str
    cardTerminalId: str
    cardTerminalMacAddress: str | None
    cardhandle: str
    commonName: str | None
    expirationDate: int
    hasEccCert: bool
    hasRsaCert: bool
    iccsn: str
    insertTime: int
    slotNo: int
    telematikId: str | None
    type: str
    version: CardVersion
