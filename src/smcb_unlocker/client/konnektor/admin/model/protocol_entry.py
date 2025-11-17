from pydantic import BaseModel


class ProtocolEntry(BaseModel):
    type: str
    timestamp: str
    timestampAsDateTime: str
    severity: str
    message: str
    bytes: str
