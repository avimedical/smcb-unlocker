import asyncio
import logging
import ssl

from websockets.asyncio.client import connect

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

    konnektor_ready: asyncio.Event
    kt_ready: asyncio.Event
    
    def __init__(self, base_url: str, mgmt_username: str, mgmt_password: str):
        self.base_url = base_url
        self.mgmt_username = mgmt_username
        self.mgmt_password = mgmt_password

    @staticmethod
    def of(base_url: str, mgmt_username: str, mgmt_password: str) -> KtSmcbVerifier:
        return KtSmcbVerifier(base_url, mgmt_username, mgmt_password)

    def connect(self, konnektor_ready: asyncio.Event, kt_ready: asyncio.Event):
        self.konnektor_ready = konnektor_ready
        self.kt_ready = kt_ready

    def ensure_connected(self):
        if not self.kt_ready or not self.konnektor_ready:
            raise RuntimeError("KtSmcbVerifier and KonnektorSmcbVerifier are not connected. Call 'connect' method first.")

    def get_ssl_context(self) -> ssl.SSLContext | None:
        if self.base_url.startswith("wss://"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        else:
            return None

    async def get_smcb_key(self) -> str:
        async with connect(self.base_url, subprotocols=[WS_MGMT_PROTOCOL], ssl=self.get_ssl_context()) as ws:
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
        async with connect(self.base_url, subprotocols=[WS_SMCB_PROTOCOL], ssl=self.get_ssl_context()) as ws:
            state_machine = StateMachine(ws, smcb_key, smcb_pin)
            async for state in state_machine.run():
                if isinstance(state, Authenticated):
                    self.kt_ready.set()

        return True

    async def run(self, smcb_pin: str) -> bool:
        self.ensure_connected()

        smcb_key = await self.get_smcb_key()
        await self.konnektor_ready.wait()
        result = await self.verify_smcb(smcb_key, smcb_pin)

        return result
