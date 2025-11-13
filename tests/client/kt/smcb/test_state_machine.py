import websockets

from smcb_unlocker.client.kt.smcb.model import (
    AuthenticateRequest,
    AuthenticateRequestPayload,
    AuthenticateResponse,
    Header,
    InputPinRequest,
    InputPinRequestPayload,
    InputPinResponse,
    Notify,
    NotifyPayload,
    OutputRequest,
    OutputRequestPayload,
    OutputResponse,
    WsModel,
)
from smcb_unlocker.client.kt.smcb.states import End
from smcb_unlocker.client.kt.smcb.state_machine import StateMachine


async def test_state_machine():
    """Test the SMC-B authentication state machine with a mock websocket server.

    The test simulates a full authentication flow, which includes the following messages:
    1. Server: AuthenticateRequest
    2. Client: AuthenticateResponse
    3. Server: Notify (authentication success)
    4. Server: InputPinRequest
    5. Client: InputPinResponse
    6. Server: Notify (PIN accepted)
    7. Server: OutputRequest
    8. Client: OutputResponse
    """

    async def server_handler(ws: websockets.ServerConnection):
        auth_req = AuthenticateRequest(Header=Header(MsgId="1"), PayloadType="AuthenticateRequest", Payload=AuthenticateRequestPayload(ApiVersion="1.0", Challenge="0a0b0c0d"))
        notify_auth = Notify(Header=Header(MsgId="2", SessionId="s1"), PayloadType="Notify", Payload=NotifyPayload(Code=0))
        input_pin_payload = InputPinRequestPayload(Slot="slot1", Atr="atr", Prompt="prompt", Message="message", MessageType="type", MinLen=4, MaxLen=8, TimeoutFirst=30, TimeoutOther=10, TimeoutAll=60, OkButton=True, CancelButton=True)
        input_pin_req = InputPinRequest(Header=Header(MsgId="3", SessionId="s1"), PayloadType="InputPinRequest", Payload=input_pin_payload)
        notify_pin = Notify(Header=Header(MsgId="4", SessionId="s1"), PayloadType="Notify", Payload=NotifyPayload(Code=0))
        output_req_payload = OutputRequestPayload(Slot="slot1", Atr="atr", Message="success", MessageType="type", MessageCode="code", Timeout=30, OkButton=False, CancelButton=False, ExpectResponse=False)
        output_req = OutputRequest(Header=Header(MsgId="5", SessionId="s1"), PayloadType="OutputRequest", Payload=output_req_payload)

        to_recv = [
            AuthenticateResponse,
            InputPinResponse,
            OutputResponse,
        ]

        await ws.send(auth_req.model_dump_json(exclude_none=True))

        async for msg_json in ws:
            msg_recv = WsModel.model_validate_json(f'{{"msg": {msg_json}}}').msg
            expected_cls = to_recv.pop(0)
            assert isinstance(msg_recv, expected_cls)

            if isinstance(msg_recv, AuthenticateResponse):
                await ws.send(notify_auth.model_dump_json(exclude_none=True))
                await ws.send(input_pin_req.model_dump_json(exclude_none=True))
            elif isinstance(msg_recv, InputPinResponse):
                await ws.send(notify_pin.model_dump_json(exclude_none=True))
                await ws.send(output_req.model_dump_json(exclude_none=True))
            elif isinstance(msg_recv, OutputResponse):
                break
    
    async with websockets.serve(server_handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()

        async with websockets.connect(f"ws://{host}:{port}") as ws:
            state_machine = StateMachine(ws, "0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d0a0b0c0d", "12345678")
            
            state = None
            async for s in state_machine.run():
                state = s

            assert isinstance(state, End)
