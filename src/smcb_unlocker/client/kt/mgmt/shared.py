import uuid

from pydantic import BaseModel


class Header(BaseModel):
    msgId: str
    inReplyToId: str | None = None
    sessionId: str | None = None


def get_id() -> str:
    return uuid.uuid4().hex
