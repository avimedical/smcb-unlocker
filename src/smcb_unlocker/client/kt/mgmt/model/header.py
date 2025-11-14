from pydantic import BaseModel


class Header(BaseModel):
    msgId: str
    inReplyToId: str | None = None
    sessionId: str | None = None
