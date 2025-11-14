import asyncio

import websockets

from smcb_unlocker.client.kt.mgmt.model import (
    LoginRequest,
    LoginResponse,
    LoginResponsePayload,
    GetApiVersionRequest,
    GetApiVersionResponse,
    GetApiVersionResponsePayload,
    Header as MgmtHeader,
    LogoutRequest,
    LogoutResponse,
    LogoutResponsePayload,
    SmcbAuthenticationRequest,
    SmcbAuthenticationResponse,
    SmcbAuthenticationResponsePayload,
    WsModel as MgmtWsModel,
)
from smcb_unlocker.client.kt.smcb.model import (
    AuthenticateRequest,
    AuthenticateRequestPayload,
    AuthenticateResponse,
    Header as SmcbHeader,
    InputPinRequest,
    InputPinRequestPayload,
    InputPinResponse,
    Notify,
    NotifyPayload,
    OutputRequest,
    OutputRequestPayload,
    WsModel as SmcbWsModel,
)
from smcb_unlocker.worker.verify.kt_smcb_verifier import KtSmcbVerifier


async def test_kt_smcb_verifier_runs():
    recv_queue = asyncio.Queue()

    async def mgmt_server_handler(ws: websockets.ServerConnection):
        """Mock management websocket server for testing KtSmcbVerifier."""
        get_api_version_res = GetApiVersionResponse(header=MgmtHeader(msgId="1"), payloadType="GetApiVersionResponse", payload=GetApiVersionResponsePayload(apiVersion="1.0"))
        login_res = LoginResponse(header=MgmtHeader(msgId="2"), payloadType="LoginResponse", payload=LoginResponsePayload(sessionId="session1"))
        smcb_auth_res = SmcbAuthenticationResponse(header=MgmtHeader(msgId="3", sessionId="session1"), payloadType="SmcbAuthenticationResponse", payload=SmcbAuthenticationResponsePayload(key="0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d"))
        logout_res = LogoutResponse(header=MgmtHeader(msgId="4", sessionId="session1"), payloadType="LogoutResponse", payload=LogoutResponsePayload())

        async for msg_json in ws:
            msg_recv = MgmtWsModel.model_validate_json(f'{{"msg": {msg_json}}}').msg
            await recv_queue.put(msg_recv)

            if isinstance(msg_recv, GetApiVersionRequest):
                await ws.send(get_api_version_res.model_dump_json(exclude_none=True))
            elif isinstance(msg_recv, LoginRequest):
                await ws.send(login_res.model_dump_json(exclude_none=True))
            elif isinstance(msg_recv, SmcbAuthenticationRequest):
                await ws.send(smcb_auth_res.model_dump_json(exclude_none=True))
            elif isinstance(msg_recv, LogoutRequest):
                await ws.send(logout_res.model_dump_json(exclude_none=True))

    async def smcb_server_handler(ws: websockets.ServerConnection):
        auth_req = AuthenticateRequest(Header=SmcbHeader(MsgId="1"), PayloadType="AuthenticateRequest", Payload=AuthenticateRequestPayload(ApiVersion="1.0", Challenge="0a0b0c0d"))
        notify_auth = Notify(Header=SmcbHeader(MsgId="2", SessionId="s1"), PayloadType="Notify", Payload=NotifyPayload(Code=0))
        input_pin_payload = InputPinRequestPayload(Slot="slot1", Atr="atr", Prompt="prompt", Message="message", MessageType="type", MinLen=4, MaxLen=8, TimeoutFirst=30, TimeoutOther=10, TimeoutAll=60, OkButton=True, CancelButton=True)
        input_pin_req = InputPinRequest(Header=SmcbHeader(MsgId="3", SessionId="s1"), PayloadType="InputPinRequest", Payload=input_pin_payload)
        notify_pin = Notify(Header=SmcbHeader(MsgId="4", SessionId="s1"), PayloadType="Notify", Payload=NotifyPayload(Code=0))
        output_req_payload = OutputRequestPayload(Slot="slot1", Atr="atr", Message="success", MessageType="type", MessageCode="code", Timeout=30, OkButton=False, CancelButton=False, ExpectResponse=False)
        output_req = OutputRequest(Header=SmcbHeader(MsgId="5", SessionId="s1"), PayloadType="OutputRequest", Payload=output_req_payload)

        await ws.send(auth_req.model_dump_json(exclude_none=True))

        async for msg_json in ws:
            msg_recv = SmcbWsModel.model_validate_json(f'{{"msg": {msg_json}}}').msg
            await recv_queue.put(msg_recv)

            if isinstance(msg_recv, AuthenticateResponse):
                await ws.send(notify_auth.model_dump_json(exclude_none=True))
                await ws.send(input_pin_req.model_dump_json(exclude_none=True))
            elif isinstance(msg_recv, InputPinResponse):
                await ws.send(notify_pin.model_dump_json(exclude_none=True))
                await ws.send(output_req.model_dump_json(exclude_none=True))

    async def server_handler(ws: websockets.ServerConnection):
        if ws.subprotocol == "cobra":
            await mgmt_server_handler(ws)
        elif ws.subprotocol == "cobra-smcb":
            await smcb_server_handler(ws)

    async with websockets.serve(server_handler, "127.0.0.1", 0, subprotocols=["cobra", "cobra-smcb"]) as server:
        host, port = server.sockets[0].getsockname()

        verifier = KtSmcbVerifier(
            base_url=f"ws://{host}:{port}",
            mgmt_username="admin",
            mgmt_password="password",
        )
        konnektor_ready = asyncio.Event()
        kt_ready = asyncio.Event()
        verifier.connect(konnektor_ready, kt_ready)

        async with asyncio.TaskGroup() as tg:
            task = tg.create_task(verifier.run("12345678"))

            to_recv = [
                GetApiVersionRequest,
                LoginRequest,
                SmcbAuthenticationRequest,
                LogoutRequest,
            ]
            for expected_cls in to_recv:
                async with asyncio.timeout(1):
                    msg_recv = await recv_queue.get()
                assert isinstance(msg_recv, expected_cls)

            konnektor_ready.set()
            await kt_ready.wait()

            to_recv = [
                AuthenticateResponse,
                InputPinResponse,
            ]
            for expected_cls in to_recv:
                async with asyncio.timeout(1):
                    msg_recv = await recv_queue.get()
                assert isinstance(msg_recv, expected_cls)

            result = await task
            assert result is True
