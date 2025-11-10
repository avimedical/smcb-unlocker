from pydantic import BaseModel


class Header(BaseModel):
    MsgId: str
    InReplyToId: str | None = None
    SessionId: str | None = None
