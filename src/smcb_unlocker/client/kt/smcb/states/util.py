import uuid


def get_id() -> str:
    return uuid.uuid4().hex
