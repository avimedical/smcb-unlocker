import websockets

from smcb_unlocker.client.kt.mgmt import login, LoginRequest, LoginResponse, LoginResponsePayload, Header

async def test_login():
    async def server_handler(ws: websockets.ServerConnection):
        async for msg_json in ws:
            msg_recv = LoginRequest.model_validate_json(msg_json)
            assert msg_recv.payloadType == "LoginRequest"
            assert msg_recv.payload.username == "testuser"
            assert msg_recv.payload.password == "testpass"

            msg_send = LoginResponse(
                header=Header(msgId="1", inReplyToId=msg_recv.header.msgId),
                payloadType="LoginResponse",
                payload=LoginResponsePayload(sessionId="session123")
            )
            await ws.send(msg_send.model_dump_json(exclude_none=True))

    async with websockets.serve(server_handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()

        async with websockets.connect(f"ws://{host}:{port}") as ws:
            session_id = await login(ws, "testuser", "testpass")
            assert session_id == "session123"
