import asyncio
import logging
import ssl

from websockets.asyncio.client import connect

from .config import Config
from .client.kt.mgmt import get_api_version, login, logout, smcb_authentication
from .client.kt.smcb import StateMachine
from .client.kt.smcb.states import Authenticated

SUPPORTED_API_VERSIONS = ["3.2"]
WS_MGMT_PROTOCOL = "cobra"
WS_SMCB_PROTOCOL = "cobra-smcb"


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def get_smcb_key(kt_base_url: str, kt_mgmt_username: str, kt_mgmt_password: str) -> str:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with connect(kt_base_url, subprotocols=[WS_MGMT_PROTOCOL], ssl=ssl_context) as ws:
        api_version = await get_api_version(ws)
        if api_version not in SUPPORTED_API_VERSIONS:
            log.warning(f"API version {api_version} not supported, supported versions are: {SUPPORTED_API_VERSIONS}")

        session_id = await login(ws, kt_mgmt_username, kt_mgmt_password)
        log.info(f"Logged in with session ID: {session_id}")
        
        try:
            return await smcb_authentication(ws, session_id)
        finally:
            # Avoid "Session store full" errors by logging out
            await logout(ws, session_id)
            log.info("Logged out")


async def trigger_smcb_verify(smcb_ws_authenticated: asyncio.Event):
    await smcb_ws_authenticated.wait()
    log.info("SMCB WebSocket authenticated successfully")


async def remote_smcb_verify(smcb_ws_authenticated: asyncio.Event, kt_base_url: str, smcb_key: str, smcb_pin: str):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async def on_state_change(old_state, new_state):
        if isinstance(new_state, Authenticated):
            smcb_ws_authenticated.set()

    async with connect(kt_base_url, subprotocols=[WS_SMCB_PROTOCOL], ssl=ssl_context) as ws:
        state_machine = StateMachine(ws, smcb_key, smcb_pin, on_state_change=on_state_change)
        await state_machine.run()


async def verify_smcb_pin(kt_base_url: str, smcb_key: str, smcb_pin: str):
    async with asyncio.TaskGroup() as tg:
        smcb_ws_authenticated = asyncio.Event()
        trigger_task = tg.create_task(trigger_smcb_verify(smcb_ws_authenticated))
        verfiy_task = tg.create_task(remote_smcb_verify(smcb_ws_authenticated, kt_base_url, smcb_key, smcb_pin))

    return True


async def main():
    config = Config()

    smcb_key = await get_smcb_key(config.kt_base_url, config.kt_mgmt_username, config.kt_mgmt_password)
    log.info(f"SMCB Key: {smcb_key}")

    result = await verify_smcb_pin(config.kt_base_url, smcb_key, config.smcb_pin)

if __name__ == "__main__":
    asyncio.run(main())
