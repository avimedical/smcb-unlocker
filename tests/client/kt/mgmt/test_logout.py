import websockets

from smcb_unlocker.client.kt.mgmt import logout
from smcb_unlocker.client.kt.mgmt.model import LogoutRequest, LogoutResponse, LogoutResponsePayload, Header

async def test_logout():
    async def server_handler(ws: websockets.ServerConnection):
        async for msg_json in ws:
            msg_recv = LogoutRequest.model_validate_json(msg_json)
            assert msg_recv.payloadType == "LogoutRequest"
            assert msg_recv.header.sessionId == "session123"

            msg_send = LogoutResponse(
                header=Header(msgId="1", inReplyToId=msg_recv.header.msgId, sessionId="session123"),
                payloadType="LogoutResponse",
                payload=LogoutResponsePayload()
            )
            await ws.send(msg_send.model_dump_json(exclude_none=True))

    async with websockets.serve(server_handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()

        async with websockets.connect(f"ws://{host}:{port}") as ws:
            await logout(ws, "session123")
