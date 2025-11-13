import asyncio
import logging
import ssl

from websockets.asyncio.client import connect

from smcb_unlocker.worker.verify import konnektor_smcb_verifier
from smcb_unlocker.client.kt.mgmt import get_api_version, login, logout, smcb_authentication
from smcb_unlocker.client.kt.smcb import StateMachine
from smcb_unlocker.client.kt.smcb.states import Authenticated


SUPPORTED_API_VERSIONS = ["3.2"]
WS_MGMT_PROTOCOL = "cobra"
WS_SMCB_PROTOCOL = "cobra-smcb"


log = logging.getLogger(__name__)


class KtSmcbVerifier:
    base_url: str
    mgmt_username: str
    mgmt_password: str
    
    kt_ready: asyncio.Event
    konnektor_ready: asyncio.Event
    
    def __init__(self, base_url: str, mgmt_username: str, mgmt_password: str):
        self.base_url = base_url
        self.mgmt_username = mgmt_username
        self.mgmt_password = mgmt_password

    def connect(self, other: 'konnektor_smcb_verifier.KonnektorSmcbVerifier'):
        self.kt_ready = asyncio.Event()
        other.kt_ready = self.kt_ready
        self.konnektor_ready = asyncio.Event()
        other.konnektor_ready = self.konnektor_ready

    def ensure_connected(self):
        if not self.kt_ready or not self.konnektor_ready:
            raise RuntimeError("KtSmcbVerifier and KonnektorSmcbVerifier are not connected. Call 'connect' method first.")

    async def get_smcb_key(self) -> str:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with connect(self.base_url, subprotocols=[WS_MGMT_PROTOCOL], ssl=ssl_context) as ws:
            api_version = await get_api_version(ws)
            if api_version not in SUPPORTED_API_VERSIONS:
                log.warning(f"API version {api_version} not supported, supported versions are: {SUPPORTED_API_VERSIONS}")

            session_id = await login(ws, self.mgmt_username, self.mgmt_password)
            
            try:
                return await smcb_authentication(ws, session_id)
            finally:
                # Avoid "Session store full" errors by logging out
                await logout(ws, session_id)

    async def verify_smcb(self, smcb_key: str, smcb_pin: str) -> bool:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async def on_state_change(old_state, new_state):
            if isinstance(new_state, Authenticated):
                self.kt_ready.set()

        async with connect(self.base_url, subprotocols=[WS_SMCB_PROTOCOL], ssl=ssl_context) as ws:
            state_machine = StateMachine(ws, smcb_key, smcb_pin, on_state_change=on_state_change)
            await state_machine.run()

    async def run(self, smcb_pin: str) -> bool:
        self.ensure_connected()

        smcb_key = await self.get_smcb_key()
        await self.konnektor_ready.wait()
        return await self.verify_smcb(smcb_key, smcb_pin)
