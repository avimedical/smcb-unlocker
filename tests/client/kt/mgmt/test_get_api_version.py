import websockets

from smcb_unlocker.client.kt.mgmt import get_api_version, GetApiVersionRequest, GetApiVersionResponse, GetApiVersionResponsePayload, Header

async def test_get_api_version():
    async def server_handler(ws: websockets.ServerConnection):
        async for msg_json in ws:
            msg_recv = GetApiVersionRequest.model_validate_json(msg_json)
            assert msg_recv.payloadType == "GetApiVersionRequest"

            msg_send = GetApiVersionResponse(
                header=Header(msgId="1", inReplyToId=msg_recv.header.msgId),
                payloadType="GetApiVersionResponse",
                payload=GetApiVersionResponsePayload(apiVersion="1.2.3")
            )
            await ws.send(msg_send.model_dump_json(exclude_none=True))

    async with websockets.serve(server_handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()

        async with websockets.connect(f"ws://{host}:{port}") as ws:
            api_version = await get_api_version(ws)
            assert api_version == "1.2.3"
