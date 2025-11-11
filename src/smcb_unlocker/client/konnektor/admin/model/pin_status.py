from pydantic import BaseModel


class PinStatus(BaseModel):
    retries: int | None
    status: str
