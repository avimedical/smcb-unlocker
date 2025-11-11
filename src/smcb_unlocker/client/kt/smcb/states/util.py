import uuid


NOTIFY_CODES = {
    0: "Success",
    1: "ParserError",
    2: "AuthenticationRequired",
    3: "AuthenticationDenied",
    4: "InvalidSessionId",
    5: "InvalidMessageId",
    6: "InvalidInReplyToId",
    7: "MissingInReplyToId",
    8: "InvalidChallengeResponse",
    9: "MissingPin",
    10: "InvalidPin",
    11: "InvalidPinLength",
    12: "UnexpectedPin",
    13: "InvalidOutputCode",
}


def get_id() -> str:
    return uuid.uuid4().hex
