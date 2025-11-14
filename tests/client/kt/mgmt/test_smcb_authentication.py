import websockets

from smcb_unlocker.client.kt.mgmt import smcb_authentication
from smcb_unlocker.client.kt.mgmt.model import SmcbAuthenticationRequest, SmcbAuthenticationResponse, SmcbAuthenticationResponsePayload, Header

async def test_smcb_authentication():
    async def server_handler(ws: websockets.ServerConnection):
        async for msg_json in ws:
            msg_recv = SmcbAuthenticationRequest.model_validate_json(msg_json)
            assert msg_recv.payloadType == "SmcbAuthenticationRequest"
            assert msg_recv.header.sessionId == "session123"

            msg_send = SmcbAuthenticationResponse(
                header=Header(msgId="1", inReplyToId=msg_recv.header.msgId, sessionId="session123"),
                payloadType="SmcbAuthenticationResponse",
                payload=SmcbAuthenticationResponsePayload(key="0a0b0c0d")
            )
            await ws.send(msg_send.model_dump_json(exclude_none=True))

    async with websockets.serve(server_handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()

        async with websockets.connect(f"ws://{host}:{port}") as ws:
            smcb_key = await smcb_authentication(ws, "session123")
            assert smcb_key == "0a0b0c0d"
