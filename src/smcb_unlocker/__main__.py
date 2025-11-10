import asyncio
import logging
import ssl

from websockets.asyncio.client import connect

from .config import Config
from .client.mgmt import get_api_version, login, logout, smcb_authentication
from .client.smcb import StateMachine


SUPPORTED_API_VERSIONS = ["3.2"]
WS_MGMT_PROTOCOL = "cobra"
WS_SMCB_PROTOCOL = "cobra-smcb"


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def get_smcb_key(base_url: str, mgmt_username: str, mgmt_password: str) -> str:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with connect(base_url, subprotocols=[WS_MGMT_PROTOCOL], ssl=ssl_context) as ws:
        api_version = await get_api_version(ws)
        if api_version not in SUPPORTED_API_VERSIONS:
            log.warning(f"API version {api_version} not supported, supported versions are: {SUPPORTED_API_VERSIONS}")

        session_id = await login(ws, mgmt_username, mgmt_password)
        log.info(f"Logged in with session ID: {session_id}")
        
        try:
            return await smcb_authentication(ws, session_id)
        finally:
            # Avoid "Session store full" errors by logging out
            await logout(ws, session_id)
            log.info("Logged out")


async def verify_smcb_pin(base_url: str, smcb_key: str, pin: str):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with connect(base_url, subprotocols=[WS_SMCB_PROTOCOL], ssl=ssl_context) as ws:
        state_machine = StateMachine(ws, smcb_key, pin)
        await state_machine.run()


async def main():
    config = Config()

    smcb_key = await get_smcb_key(config.base_url, config.mgmt_username, config.mgmt_password)
    log.info(f"SMCB Key: {smcb_key}")

    result = await verify_smcb_pin(config.base_url, smcb_key, config.smcb_pin)


if __name__ == "__main__":
    asyncio.run(main())
